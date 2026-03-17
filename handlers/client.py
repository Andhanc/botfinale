# [file name]: client.py
from pathlib import Path
from typing import Any, Dict

from aiogram import F, types
from aiogram.enums import ContentType
from aiogram.types import FSInputFile
from aiogram.exceptions import TelegramBadRequest, TelegramNetworkError
from aiogram.filters import Command, Filter
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder

from config import ADMIN_ID
from database.models import Algorithm, Manufacturer
from keyboards.calculator_kb import CalculatorKB
from keyboards.client_kb import ClientKB
from signature import Settings
from utils.ai_service import ask_ishushka, create_chat
from utils.calculator import MiningCalculator
from utils.coin_service import CoinGeckoService
from utils.states import BetterPriceState, CalculatorState, FreeAiState, SellForm

user_chats: Dict[int, str] = {}


class ChannelFilter(Filter):
    def __init__(self, channel_id: int):
        self.channel_id = channel_id

    async def __call__(self, message: types.Message) -> bool:
        return message.chat.id == self.channel_id


class Client:
    def __init__(self, bot: Settings):
        self.bot = bot.bot
        self.dp = bot.dp
        self.settings = bot
        self.user_req = bot.user_req
        self.calculator_req = bot.calculator_req
        self.coin_req = bot.coin_req
        self.sell_req = bot.sell_req
        self.guide_req = bot.guide_req
        self.latest_price_link = None

    def _get_coin_filter_rules(self) -> dict:
        """Возвращает правила фильтрации монет для определенных майнеров"""
        return {
            (Manufacturer.BITMAIN, "E9"): "ETC",
            (Manufacturer.BITMAIN, "L7"): "LTC",
            (Manufacturer.BITMAIN, "L9"): "LTC",
            (Manufacturer.BITMAIN, "S19"): "BTC",
            (Manufacturer.BITMAIN, "S21"): "BTC",
            (Manufacturer.BITMAIN, "T21"): "BTC",
            (Manufacturer.WHATSMINER, "M30"): "BTC",
            (Manufacturer.WHATSMINER, "M50"): "BTC",
            (Manufacturer.WHATSMINER, "M60"): "BTC",
            (Manufacturer.WHATSMINER, "M61"): "BTC",
            (Manufacturer.IPOLLO, "iPollo"): "ETC",
        }

    async def _filter_coins_for_miner(
        self, model_line, all_coins: list
    ) -> list:
        """Фильтрует монеты для майнера согласно правилам"""
        filter_rules = self._get_coin_filter_rules()
        filter_key = (model_line.manufacturer, model_line.name)
        
        if filter_key in filter_rules:
            # Оставляем только указанную монету
            target_coin = filter_rules[filter_key]
            filtered = [c for c in all_coins if c["symbol"] == target_coin]
            return filtered if filtered else all_coins
        else:
            # Нет правила фильтрации - оставляем все монеты
            return all_coins

    def _filter_coin_string_for_miner(
        self, model_line, coin_string: str
    ) -> str:
        """Фильтрует строку монет для майнера согласно правилам (для отображения)"""
        if not coin_string or not coin_string.strip():
            return coin_string
        
        filter_rules = self._get_coin_filter_rules()
        filter_key = (model_line.manufacturer, model_line.name)
        
        if filter_key in filter_rules:
            # Оставляем только указанную монету
            target_coin = filter_rules[filter_key]
            # Разбиваем строку на монеты и ищем нужную
            coins = [c.strip().upper() for c in coin_string.split(",")]
            if target_coin in coins:
                return target_coin
            else:
                # Если целевая монета не найдена, возвращаем исходную строку
                return coin_string
        else:
            # Нет правила фильтрации - возвращаем все монеты
            return coin_string

    async def register_handlers(self):
        self.dp.message(Command("start"))(self.start_handler)
        self.dp.message(Command("sell"))(self.sell_start_handler)
        self.dp.callback_query(F.data == "sell_device")(self.sell_start_handler_call)
        self.dp.message(Command("by"))(self.by_handler)
        self.dp.message(Command("faq"))(self.faq_handler)

        self.dp.channel_post(ChannelFilter(-1001546174824))(
            self.channel_message_handler
        )

        self.dp.callback_query(F.data == "back_main")(self.start_handler)
        self.dp.callback_query(F.data == "calc_income")(self.calc_income_handler)
        self.dp.callback_query(F.data == "price_list")(self.price_list_handler)
        self.dp.callback_query(F.data == "profile")(self.profile_handler)
        self.dp.callback_query(F.data == "calc_calc")(self.calc_calc_handler)
        self.dp.callback_query(F.data == "calc_chars")(self.calc_chars_handler)
        self.dp.callback_query(F.data == "calc_coins")(self.calc_coins_handler)

        self.dp.callback_query(F.data == "better_price")(self.better_price_handler)
        self.dp.message(
            BetterPriceState.waiting_photo,
            F.content_type == ContentType.PHOTO,
        )(self.receive_better_price_photo)
        self.dp.message(
            BetterPriceState.waiting_comment,
            F.content_type == ContentType.TEXT,
        )(self.receive_better_price_comment)
        self.dp.callback_query(
            F.data.in_({"send_bp", "cancel_bp"}),
            BetterPriceState.waiting_confirm,
        )(self.confirm_better_price)

        self.dp.callback_query(F.data == "ai_consult")(self.ai_consult_start)
        self.dp.message(FreeAiState.chat)(self.ai_chat_handler)

        self.dp.callback_query(F.data.startswith("calc_method:"))(
            self.calc_method_handler
        )
        self.dp.callback_query(F.data.startswith("calc_manufacturer:"))(
            self.calc_manufacturer_handler
        )
        self.dp.callback_query(F.data.startswith("calc_line:"))(
            self.calc_model_line_handler
        )
        self.dp.callback_query(F.data.startswith("calc_model:"))(
            self.calc_model_handler
        )
        self.dp.callback_query(F.data.startswith("calc_lines_page:"))(
            self.calc_models_page_handler
        )
        self.dp.callback_query(F.data.startswith("calc_models_page:"))(
            self.calc_models_page_handler
        )
        self.dp.callback_query(F.data == "calc_usd")(self.calc_usd_handler)
        self.dp.callback_query(F.data.startswith("calc_algorithm:"))(
            self.calc_algorithm_handler
        )
        self.dp.callback_query(F.data == "back_calc_method")(self.calc_calc_handler)
        self.dp.callback_query(F.data == "back_calc_manufacturer")(
            self.back_calc_manufacturer_handler
        )
        self.dp.callback_query(F.data == "back_calc_line")(self.back_calc_line_handler)
        self.dp.callback_query(F.data == "back_calc_model")(
            self.back_calc_model_handler
        )
        self.dp.callback_query(F.data == "back_calc_algorithm")(
            self.back_calc_algorithm_handler
        )
        self.dp.callback_query(F.data == "back_calc_hashrate")(
            self.back_calc_hashrate_handler
        )
        self.dp.callback_query(F.data == "calc_rub")(self.calc_rub_handler)

        self.dp.message(CalculatorState.input_electricity_price)(
            self.calc_electricity_handler
        )
        self.dp.message(CalculatorState.input_hashrate)(self.calc_hashrate_handler)
        self.dp.message(CalculatorState.input_power)(self.calc_power_handler)

        # Обработчики для формы продажи оборудования
        # Регистрируем без фильтра content_type, проверка будет внутри обработчиков
        self.dp.message(SellForm.device)(self.sell_device_handler)
        self.dp.message(SellForm.price)(self.sell_price_handler)
        self.dp.message(SellForm.condition)(self.sell_condition_handler)
        self.dp.message(SellForm.description)(self.sell_description_handler)
        self.dp.message(SellForm.contact)(self.sell_contact_handler)

        self.dp.callback_query(F.data.startswith("chars_manufacturer:"))(
            self.chars_manufacturer_handler
        )
        self.dp.callback_query(F.data.startswith("chars_model:"))(
            self.chars_model_handler
        )
        self.dp.callback_query(F.data == "back_chars_models")(
            self.back_chars_models_handler
        )
        self.dp.callback_query(F.data.startswith("chars_line:"))(
            self.chars_model_line_handler
        )
        self.dp.callback_query(F.data == "back_chars_lines")(
            self.back_chars_lines_handler
        )

    async def channel_message_handler(self, message: types.Message):
        try:
            if message.text and "АКТУАЛЬНЫЙ ПРАЙС" in message.text.upper():
                channel_username = message.chat.username
                message_id = message.message_id

                if message.chat.username:
                    link = f"https://t.me/{channel_username}/{message_id}"
                else:
                    id_channel = f"{message.chat.id}"
                    link = f"https://t.me/c/{id_channel.split('-100')[1]}/{message_id}"
                await self.calculator_req.update_link(link)
                print(f"Обнаружен актуальный прайс: {link}")

        except Exception as e:
            print(f"Ошибка при обработке сообщения из канала: {e}")

    async def start_handler(
        self, message: types.Message | types.CallbackQuery, state: FSMContext
    ):
        await state.clear()
        if isinstance(message, types.CallbackQuery):
            user = message.from_user
            message_obj = message.message
            try:
                await message.answer()
            except TelegramBadRequest:
                pass
        else:
            user = message.from_user
            message_obj = message

        if not await self.user_req.user_exists(user.id):
            await self.user_req.add_user(user.id, user.username or user.first_name)

        text = (
            f"👋 Привет, {user.first_name}!\n\n"
            "Я — ваш AI-помощник в сфере майнинга криптовалют. "
            "Могу провести расчёт потенциальной доходности, помочь с выбором подходящего оборудования "
            "и дать подробные ответы на любые связанные с этим вопросы."
        )
        # Логотип из папки проекта (относительный путь — работает на любом сервере)
        project_root = Path(__file__).resolve().parent.parent
        welcome_photo = FSInputFile(project_root / "image" / "logo.JPG")
        kb = await ClientKB.main_menu()

        if isinstance(message, types.CallbackQuery):
            await message_obj.delete()
        await self.bot.send_photo(
            chat_id=user.id,
            photo=welcome_photo,
            caption=text,
            reply_markup=kb,
            request_timeout=10,
        )

    async def calc_income_handler(self, call: types.CallbackQuery, state: FSMContext):
        await state.clear()
        await call.message.delete()
        kb = await ClientKB.calc_menu()
        await self.bot.send_message(
            call.from_user.id, "💰 Выберите нужный раздел:", reply_markup=kb
        )
        try:
            await call.answer()
        except TelegramBadRequest:
            pass

    async def price_list_handler(self, call: types.CallbackQuery):
        try:
            # Сразу перекидываем пользователя на канал с прайс-листом
            channel_url = "https://t.me/asic_mining_store"
            await call.answer(url=channel_url)
        except Exception as e:
            print(f"Ошибка при открытии канала: {e}")
            # Если не удалось открыть через answer, отправляем сообщение с кнопкой
            try:
                builder = InlineKeyboardBuilder()
                builder.button(text="📋 Перейти к прайс-листу", url=channel_url)
                await call.message.answer(
                    "📋 Нажмите на кнопку, чтобы перейти к актуальному прайс-листу:",
                    reply_markup=builder.as_markup()
                )
                await call.answer()
            except TelegramBadRequest:
                pass

    async def profile_handler(self, call: types.CallbackQuery):
        await call.message.delete()
        kb = await ClientKB.profile_menu()
        await self.bot.send_message(
            call.from_user.id, "👤 Ваш профиль:", reply_markup=kb
        )
        try:
            await call.answer()
        except TelegramBadRequest:
            pass

    async def calc_calc_handler(self, call: types.CallbackQuery, state: FSMContext):
        await state.clear()
        await call.message.edit_text(
            "⚙️ Выберите способ расчета:",
            reply_markup=await CalculatorKB.choose_method(),
        )
        try:
            await call.answer()
        except TelegramBadRequest:
            pass

    async def calc_chars_handler(self, call: types.CallbackQuery, state: FSMContext):
        await state.clear()
        await call.message.edit_text(
            "🏭 Выберите производителя:",
            reply_markup=await ClientKB.chars_manufacturer(),
        )
        try:
            await call.answer()
        except TelegramBadRequest:
            pass

    async def chars_manufacturer_handler(
        self, call: types.CallbackQuery, state: FSMContext
    ):
        manufacturer_name = call.data.split(":")[1]
        manufacturer = Manufacturer(manufacturer_name)

        model_lines = await self.calculator_req.get_model_lines_by_manufacturer(
            manufacturer
        )
        if not model_lines:
            await call.message.edit_text(
                "❌ Нет модельных линеек для этого производителя"
            )
            try:
                await call.answer()
            except TelegramBadRequest:
                pass
            return

        await state.update_data(manufacturer=manufacturer)
        await call.message.edit_text(
            f"📱 Выберите модельную линейку {manufacturer.value}:",
            reply_markup=await ClientKB.chars_model_lines(model_lines),
        )
        try:
            await call.answer()
        except TelegramBadRequest:
            pass

    async def chars_model_line_handler(
        self, call: types.CallbackQuery, state: FSMContext
    ):
        model_line_id = int(call.data.split(":")[1])
        model_line = await self.calculator_req.get_model_line_by_id(model_line_id)

        if not model_line:
            await call.message.edit_text("❌ Модельная линейка не найдена")
            try:
                await call.answer()
            except TelegramBadRequest:
                pass
            return

        models = await self.calculator_req.get_asic_models_by_model_line(model_line_id)
        if not models:
            await call.message.edit_text("❌ Нет моделей для этой линейки")
            try:
                await call.answer()
            except TelegramBadRequest:
                pass
            return

        await state.update_data(model_line=model_line)
        await call.message.edit_text(
            f"🔧 Выберите модель {model_line.manufacturer.value} {model_line.name}:",
            reply_markup=await ClientKB.chars_models(models),
        )
        try:
            await call.answer()
        except TelegramBadRequest:
            pass

    async def chars_model_handler(self, call: types.CallbackQuery, state: FSMContext):
        model_id = int(call.data.split(":")[1])

        model = await self.calculator_req.get_asic_model_by_id(model_id)
        if not model:
            await call.message.edit_text("❌ Модель не найдена")
            try:
                await call.answer()
            except TelegramBadRequest:
                pass
            return

        model_line = await self.calculator_req.get_model_line_by_id(model.model_line_id)
        if not model_line:
            await call.message.edit_text("❌ Информация о модельной линейке не найдена")
            try:
                await call.answer()
            except TelegramBadRequest:
                pass
            return

        message = (
            f"🔧 **{model_line.manufacturer.value} {model.name}**\n\n"
            f"⚙️ **Алгоритм:** {model_line.algorithm.value}\n"
            f"⚡ **Хешрейт:** {model.hash_rate} {'TH/s' if model.hash_rate > 1 else 'GH/s'}\n"
            f"🔌 **Потребление:** {model.power_consumption}W\n"
        )

        if model.get_coin:
            # Применяем фильтрацию монет согласно правилам
            filtered_coins = self._filter_coin_string_for_miner(model_line, model.get_coin)
            message += f"🪙 **Добывает:** {filtered_coins}\n"

        await call.message.edit_text(message, reply_markup=await ClientKB.chars_back())
        try:
            await call.answer()
        except TelegramBadRequest:
            pass

    async def back_chars_models_handler(
        self, call: types.CallbackQuery, state: FSMContext
    ):
        try:
            data = await state.get_data()
            manufacturer = data["manufacturer"]

            model_lines = await self.calculator_req.get_model_lines_by_manufacturer(
                manufacturer
            )

            await call.message.edit_text(
                f"📱 Выберите модельную линейку {manufacturer.value}:",
                reply_markup=await ClientKB.chars_model_lines(model_lines),
            )
        except TelegramBadRequest as e:
            if "message is not modified" not in str(e):
                raise
        finally:
            try:
                await call.answer()
            except TelegramBadRequest:
                pass

    async def calc_coins_handler(self, call: types.CallbackQuery):
        coins = await self.coin_req.get_all_coins()
        if not coins:
            await call.message.edit_text("❌ Нет данных о ценах монет")
            try:
                await call.answer()
            except TelegramBadRequest:
                pass
            return

        # Получаем актуальный курс доллара (USDT/RUB) через CoinGecko
        coin_service = CoinGeckoService(self.settings)
        usd_to_rub = await coin_service.get_usd_rub_rate()

        priority_order = ["BTC", "ETH", "LTC", "DOGE", "KAS"]
        
        filtered_coins = [coin for coin in coins if coin.symbol in priority_order]
        
        priority_dict = {symbol: index for index, symbol in enumerate(priority_order)}
        sorted_coins = sorted(filtered_coins, key=lambda coin: priority_dict[coin.symbol])

        message = "💎 Текущие цены монет:\n\n"
        message += f"🔄 Курс доллара: 1 USDT ≈ {usd_to_rub:.2f} RUB\n\n"
        for coin in sorted_coins:
            change_icon = "📈" if coin.price_change_24h >= 0 else "📉"
            message += (
                f"🔸 {coin.symbol} ({coin.name})\n"
                f"   💵 ${coin.current_price_usd:,.2f} | ₽{coin.current_price_rub:,.0f}\n"
                f"   {change_icon} {coin.price_change_24h:+.1f}%\n\n"
            )

        await call.message.edit_text(message, reply_markup=await ClientKB.back_calc())
        try:
            await call.answer()
        except TelegramBadRequest:
            pass

    async def better_price_handler(self, call: types.CallbackQuery, state: FSMContext):
        await call.message.delete()
        await self.bot.send_message(
            call.from_user.id,
            "📸 Пришлите скриншот с ценой конкурента:",
        )
        await state.set_state(BetterPriceState.waiting_photo)
        try:
            await call.answer()
        except TelegramBadRequest:
            pass

    async def receive_better_price_photo(
        self, message: types.Message, state: FSMContext
    ):
        photo_file_id = message.photo[-1].file_id
        await state.update_data(photo=photo_file_id)
        await message.answer("💬 Добавьте комментарий (что именно хотите изменить):")
        await state.set_state(BetterPriceState.waiting_comment)

    async def receive_better_price_comment(
        self, message: types.Message, state: FSMContext
    ):
        await state.update_data(comment=message.text)
        data = await state.get_data()

        await message.answer_photo(
            photo=data["photo"],
            caption=f"<b>Предпросмотр:</b>\n\n{data['comment']}\n\nОт: @{message.from_user.username or message.from_user.first_name}",
            parse_mode="HTML",
            reply_markup=await ClientKB.confirm_a(),
        )
        await state.set_state(BetterPriceState.waiting_confirm)

    async def confirm_better_price(self, call: types.CallbackQuery, state: FSMContext):
        try:
            await call.answer()
        except TelegramBadRequest:
            pass

        if call.data == "cancel_bp":
            await call.message.edit_caption(caption="Отменено.")
            await state.clear()
            return

        data = await state.get_data()
        user = call.from_user
        try:
            await self.bot.send_photo(
                chat_id=ADMIN_ID,
                photo=data["photo"],
                caption=(
                    f"<b>Заявка «Лучшая цена»</b>\n"
                    f"От: @{user.username or user.first_name}\n"
                    f"ID: <code>{user.id}</code>\n\n"
                    f"{data['comment']}\n\n"
                    f"С вами скоро свяжется менеджер @snooby37."
                ),
                parse_mode="HTML",
                request_timeout=15,
            )
        except (TelegramNetworkError, OSError) as e:
            print(f"Сеть при отправке заявки админу: {e}")
            await self.bot.send_message(
                ADMIN_ID,
                f"⚠ Заявка «Лучшая цена» (не удалось отправить фото):\n"
                f"От: @{user.username or user.first_name}, ID: {user.id}\n\n{data['comment']}",
            )
        except Exception as e:
            print(e)
            await call.message.edit_caption(
                caption="❌ Не удалось отправить заявку. Попробуйте позже."
            )
            await state.clear()
            return

        await call.message.edit_caption(
            caption="✅ Спасибо! С вами скоро свяжется менеджер @snooby37.",
            parse_mode=None,
        )
        await state.clear()

    async def by_handler(self, message: types.Message):
        guide = await self.guide_req.get_guide()
        if guide:
            message_text = f"📖 {guide.title}\n\n{guide.content}"
            await message.answer(message_text)
        else:
            await message.answer("❌ Гайд пока недоступен")

    async def faq_handler(self, message: types.Message):
        await message.answer(
            """📦 <b>Мы отправляем оборудование:</b>

<blockquote>
— Любой удобной вам ТК (<b>СДЭК</b>, <b>Деловые Линии</b> и т.д.)
— Можно забрать лично в офисе
— Или через вашего гаранта
</blockquote>

<b>💰 Оплатить можно:</b>

<blockquote>
— <b>Наличными</b> при встрече
— Криптой (<b>USDT</b>) — актуальный курс подскажет менеджер
</blockquote>

👨‍💼 Менеджер: <a href="https://t.me/snooby37">@snooby37</a>
📢 Канал: <a href="https://t.me/asic_mining_store">@asic_mining_store</a>
""",
            parse_mode="HTML",
            disable_web_page_preview=True,
            reply_markup=await ClientKB.back_ai(),
        )

    async def ai_consult_start(self, call: types.CallbackQuery, state: FSMContext):
        await call.message.delete()
        user_id = call.from_user.id
        # Создаём новый чат в API (старые conversation_id живут 48ч и дают 404)
        conv_id = await create_chat()
        if conv_id:
            user_chats[user_id] = conv_id
        await self.bot.send_message(
            user_id,
            "💬 Задайте ваш вопрос по майнингу:",
            reply_markup=await ClientKB.back_ai(),
        )
        await state.set_state(FreeAiState.chat)
        try:
            await call.answer()
        except TelegramBadRequest:
            pass

    async def prepare_ai_context(self) -> Dict[str, Any]:
        context = {
            "asic_models": [],
            "coins": [],
            "usd_rub_rate": 80.0,
        }

        try:
            models = await self.calculator_req.get_all_asic_models()
            for model in models:
                model_line = await self.calculator_req.get_model_line_by_id(
                    model.model_line_id
                )
                context["asic_models"].append(
                    {
                        "name": model.name,
                        "manufacturer": (
                            model_line.manufacturer.value if model_line else "Unknown"
                        ),
                        "hash_rate": model.hash_rate,
                        "power": model.power_consumption,
                        "algorithm": (
                            model_line.algorithm.value if model_line else "Unknown"
                        ),
                    }
                )

            coins = await self.coin_req.get_all_coins()
            for coin in coins:
                context["coins"].append(
                    {
                        "symbol": coin.symbol,
                        "name": coin.name,
                        "price": coin.current_price_usd,
                        "price_rub": coin.current_price_rub,
                    }
                )

            coin_service = CoinGeckoService(self.settings)
            context["usd_rub_rate"] = await coin_service.get_usd_rub_rate()

        except Exception as e:
            print(f"Ошибка при подготовке контекста для AI: {e}")

        return context

    async def ai_chat_handler(self, message: types.Message, state: FSMContext):
        context = await self.prepare_ai_context()
        user_id = message.from_user.id
        # Используем чат пользователя или создаём новый; без id запрос уйдёт в fallback /request/
        conv_id = user_chats.get(user_id)
        if not conv_id:
            conv_id = await create_chat()
            if conv_id:
                user_chats[user_id] = conv_id
        response = await ask_ishushka(conv_id or "default", message.text, context)
        await message.answer(
            response, parse_mode=None, reply_markup=await ClientKB.back_ai()
        )

    async def calc_method_handler(self, call: types.CallbackQuery, state: FSMContext):
        method = call.data.split(":")[1]
        await state.update_data(method=method)

        if method == "asic":
            await call.message.edit_text(
                "🏭 Выберите производителя:",
                reply_markup=await CalculatorKB.choose_manufacturer(),
            )
        elif method == "hashrate":
            await call.message.edit_text(
                "⚙️ Выберите алгоритм:",
                reply_markup=await CalculatorKB.choose_algorithm(),
            )
        try:
            await call.answer()
        except TelegramBadRequest:
            pass

    async def calc_manufacturer_handler(
        self, call: types.CallbackQuery, state: FSMContext
    ):
        manufacturer_name = call.data.split(":")[1]
        manufacturer = Manufacturer(manufacturer_name)

        model_lines = await self.calculator_req.get_model_lines_by_manufacturer(
            manufacturer
        )
        if not model_lines:
            await call.message.edit_text(
                "❌ Нет модельных линеек для этого производителя"
            )
            try:
                await call.answer()
            except TelegramBadRequest:
                pass
            return

        await state.update_data(manufacturer=manufacturer)
        await call.message.edit_text(
            f"📱 Выберите модельную линейку {manufacturer.value}:",
            reply_markup=await CalculatorKB.choose_model_lines(model_lines, page=0),
        )
        try:
            await call.answer()
        except TelegramBadRequest:
            pass

    async def calc_model_line_handler(
        self, call: types.CallbackQuery, state: FSMContext
    ):
        model_line_id = int(call.data.split(":")[1])
        model_line = await self.calculator_req.get_model_line_by_id(model_line_id)
        if not model_line:
            await call.message.edit_text("❌ Модельная линейка не найдена")
            try:
                await call.answer()
            except TelegramBadRequest:
                pass
            return

        models = await self.calculator_req.get_asic_models_by_model_line(model_line_id)
        if not models:
            await call.message.edit_text("❌ Нет моделей для этой линейки")
            try:
                await call.answer()
            except TelegramBadRequest:
                pass
            return

        await state.update_data(model_line=model_line)
        await call.message.edit_text(
            f"🔧 Выберите модель {model_line.manufacturer.value} {model_line.name}:",
            reply_markup=await CalculatorKB.choose_asic_models_by_line(
                models, model_line.name, page=0
            ),
        )
        try:
            await call.answer()
        except TelegramBadRequest:
            pass

    async def calc_models_page_handler(
        self, call: types.CallbackQuery, state: FSMContext
    ):
        page = int(call.data.split(":")[1])
        data = await state.get_data()

        if "model_line" in data:
            model_line = data["model_line"]
            models = await self.calculator_req.get_asic_models_by_model_line(
                model_line.id
            )
            await call.message.edit_reply_markup(
                reply_markup=await CalculatorKB.choose_asic_models_by_line(
                    models, model_line.name, page=page
                )
            )
        else:
            manufacturer = data["manufacturer"]
            model_lines = await self.calculator_req.get_model_lines_by_manufacturer(
                manufacturer
            )
            await call.message.edit_reply_markup(
                reply_markup=await CalculatorKB.choose_model_lines(
                    model_lines, page=page
                )
            )
        try:
            await call.answer()
        except TelegramBadRequest:
            pass

    async def calc_model_handler(self, call: types.CallbackQuery, state: FSMContext):
        model_id = int(call.data.split(":")[1])
        model = await self.calculator_req.get_asic_model_by_id(model_id)
        if not model:
            await call.message.edit_text("❌ Модель не найдена")
            try:
                await call.answer()
            except TelegramBadRequest:
                pass
            return

        await state.update_data(model_id=model_id, model=model)
        await call.message.edit_text(
            "💡 Введите стоимость электроэнергии (₽/кВт·ч):",
            reply_markup=await CalculatorKB.electricity_input(),
        )
        await state.set_state(CalculatorState.input_electricity_price)
        try:
            await call.answer()
        except TelegramBadRequest:
            pass

    async def calc_algorithm_handler(
        self, call: types.CallbackQuery, state: FSMContext
    ):
        algorithm_name = call.data.split(":")[1]
        algorithm = Algorithm(algorithm_name)
        await state.update_data(algorithm=algorithm)
        
        # Определяем единицы измерения хэшрейта для каждого алгоритма
        algorithm_lower = algorithm_name.lower()
        # В базе данных ETCHASH определен как "Etchash/Ethash"
        if algorithm_lower in ["sha-256", "sha256"]:
            hashrate_unit = "TH/s"
        elif algorithm_lower in ["scrypt"]:
            hashrate_unit = "GH/s"
        elif algorithm_lower in ["etchash", "ethash", "etchash/ethash"]:
            hashrate_unit = "GH/s"  # Для Etchash вводим в GH/s
        elif algorithm_lower in ["kheavyhash"]:
            hashrate_unit = "TH/s"  # Для kHeavyHash вводим в TH/s
        elif algorithm_lower in ["blake2s"]:
            hashrate_unit = "TH/s"  # Для Blake2S вводим в TH/s
        elif algorithm_lower in ["blake2b+sha3", "blake2b_sha3"]:
            hashrate_unit = "GH/s"
        else:
            hashrate_unit = "TH/s"  # По умолчанию
        
        await call.message.edit_text(
            f"⚡ Введите ваш хешрейт ({hashrate_unit}):",
            reply_markup=await CalculatorKB.hashrate_input(),
        )
        await state.set_state(CalculatorState.input_hashrate)
        try:
            await call.answer()
        except TelegramBadRequest:
            pass

    async def calc_electricity_handler(self, message: types.Message, state: FSMContext):
        try:
            # Проверка типа данных - только текстовые сообщения
            if not message.text:
                await message.answer(
                    "❌ Пожалуйста, отправьте текстовое сообщение с стоимостью электроэнергии.",
                    reply_markup=await CalculatorKB.electricity_input(),
                )
                return
            
            try:
                electricity_price = float(message.text.replace(",", "."))
                if electricity_price <= 0:
                    raise ValueError
            except ValueError:
                await message.answer(
                    "❌ Неверный формат. Введите число больше нуля:",
                    reply_markup=await CalculatorKB.electricity_input(),
                )
                return

            await state.update_data(electricity_price=electricity_price)
            data = await state.get_data()

            coin_service = CoinGeckoService(self.settings)
            usd_to_rub = await coin_service.get_usd_rub_rate()

            if data.get("method") == "asic":
                model = data["model"]
                model_line = await self.calculator_req.get_model_line_by_id(
                    model.model_line_id
                )

                coin_data = {}
                coin_symbols = []

                if model.get_coin and model.get_coin.strip():
                    # Оптимизация: загружаем все монеты одним запросом вместо цикла
                    coin_symbols_list = [s.strip().upper() for s in model.get_coin.split(",")]
                    # Для Scrypt сразу добавляем DOGE, если есть LTC
                    if model_line.algorithm == Algorithm.SCRYPT and "LTC" in coin_symbols_list and "DOGE" not in coin_symbols_list:
                        coin_symbols_list.append("DOGE")
                    
                    coins_dict = await self.coin_req.get_coins_by_symbols(coin_symbols_list)
                    
                    # Загружаем данные алгоритмов одним запросом
                    algorithms_set = {coin.algorithm for coin in coins_dict.values() if coin}
                    algo_data_dict = await self.calculator_req.get_algorithm_data_batch(algorithms_set)
                    
                    # Формируем список монет с данными алгоритмов
                    all_coins = []
                    for coin_symbol in coin_symbols_list:
                        coin = coins_dict.get(coin_symbol)
                        if coin:
                            algo_data = algo_data_dict.get(coin.algorithm)
                            if algo_data:
                                all_coins.append({
                                    "symbol": coin_symbol,
                                    "coin": coin,
                                    "algo_data": algo_data
                                })
                    
                    # Применяем фильтрацию монет согласно правилам
                    filtered_coins = await self._filter_coins_for_miner(model_line, all_coins)
                    
                    # Формируем coin_data из отфильтрованных монет
                    for coin_info in filtered_coins:
                        coin_symbol = coin_info["symbol"]
                        coin = coin_info["coin"]
                        algo_data = coin_info["algo_data"]
                        coin_data[coin_symbol] = {
                            "price": coin.current_price_usd,
                            "network_hashrate": algo_data.network_hashrate,
                            "block_reward": algo_data.block_reward,
                            "algorithm": coin.algorithm.value.lower(),
                        }
                        coin_symbols.append(coin_symbol)
                    
                    # Для Scrypt добавляем DOGE (если есть LTC) - DOGE уже загружен выше
                    if model_line.algorithm == Algorithm.SCRYPT and "LTC" in [c["symbol"] for c in filtered_coins]:
                        doge_coin = coins_dict.get("DOGE")
                        if doge_coin and "DOGE" not in coin_data:
                            # LTC и DOGE - это разные сети, поэтому у них разные network_hashrate
                            # Для DOGE используем актуальное значение network_hashrate из capminer.ru тестов
                            # DOGE network_hashrate: ~2,958,883 GH/s (не зависит от LTC network_hashrate)
                            doge_network_hashrate = 2_958_883  # GH/s - актуальное значение для DOGE из capminer.ru
                            coin_data["DOGE"] = {
                                "price": doge_coin.current_price_usd,
                                "network_hashrate": doge_network_hashrate,  # Отдельный network_hashrate для DOGE
                                "block_reward": 10000,  # Стандартный block_reward для DOGE
                                "algorithm": model_line.algorithm.value.lower(),
                            }
                            coin_symbols.append("DOGE")
                else:
                    algo_data = await self.calculator_req.get_algorithm_data(
                        model_line.algorithm
                    )
                    coin = await self.coin_req.get_coin_by_symbol(
                        algo_data.default_coin
                    )
                    if coin and algo_data:
                        coin_data[coin.symbol] = {
                            "price": coin.current_price_usd,
                            "network_hashrate": algo_data.network_hashrate,
                            "block_reward": algo_data.block_reward,
                            "algorithm": model_line.algorithm.value.lower(),
                        }
                        coin_symbols.append(coin.symbol)
                        
                        # Для Scrypt добавляем DOGE (если default_coin LTC)
                        if model_line.algorithm == Algorithm.SCRYPT and coin.symbol == "LTC":
                            doge_coin = await self.coin_req.get_coin_by_symbol("DOGE")
                            if doge_coin:
                                # LTC и DOGE - это разные сети, поэтому у них разные network_hashrate
                                # Для DOGE используем актуальное значение network_hashrate из capminer.ru тестов
                                # DOGE network_hashrate: ~2,958,883 GH/s (не зависит от LTC network_hashrate)
                                doge_network_hashrate = 2_958_883  # GH/s - актуальное значение для DOGE из capminer.ru
                                coin_data["DOGE"] = {
                                    "price": doge_coin.current_price_usd,
                                    "network_hashrate": doge_network_hashrate,  # Отдельный network_hashrate для DOGE
                                    "block_reward": 10000,  # Стандартный block_reward для DOGE
                                    "algorithm": model_line.algorithm.value.lower(),
                                }
                                coin_symbols.append("DOGE")

                if not coin_symbols:
                    await message.answer("❌ Не удалось найти данные о монетах")
                    return

                # Передаем правильный алгоритм в калькулятор
                result = MiningCalculator.calculate_profitability(
                    hash_rate=model.hash_rate,
                    power_consumption=model.power_consumption,
                    electricity_price_rub=electricity_price,
                    coin_data=coin_data,
                    usd_to_rub=usd_to_rub,
                    algorithm=model_line.algorithm.value.lower()  # Передаем алгоритм
                )

                text = (
                    f"🔧 **Оборудование:** {model_line.manufacturer.value} {model.name}\n"
                )
                text += MiningCalculator.format_result(result, coin_symbols, usd_to_rub)

            else:
                algorithm = data["algorithm"]
                hashrate = data["hashrate"]
                power = data["power"]

                algo_data = await self.calculator_req.get_algorithm_data(algorithm)
                coin = await self.coin_req.get_coin_by_symbol(algo_data.default_coin)

                # ВАЖНО: Для Etchash хэшрейт должен быть в GH/s (как на capminer.ru)
                # Если пользователь ввел значение, думая что это TH/s, нужно конвертировать
                algorithm_lower = algorithm.value.lower()
                if algorithm_lower in ["etchash", "ethash", "etchash/ethash"]:
                    # Если значение слишком большое (больше 1000), возможно пользователь ввел в TH/s
                    # Конвертируем из TH/s в GH/s
                    if hashrate > 1000:
                        hashrate = hashrate * 1000  # TH/s -> GH/s
                    # Иначе считаем, что уже в GH/s (как на capminer.ru)

                # Формируем coin_data
                coin_data_input = {
                    coin.symbol: {
                        "price": coin.current_price_usd,
                        "network_hashrate": algo_data.network_hashrate,
                        "block_reward": algo_data.block_reward,
                        "algorithm": algorithm.value.lower(),
                    }
                }
                
                # Для Scrypt добавляем DOGE (если default_coin LTC)
                display_symbols = [coin.symbol]
                if algorithm == Algorithm.SCRYPT and coin.symbol == "LTC":
                    doge_coin = await self.coin_req.get_coin_by_symbol("DOGE")
                    if doge_coin:
                        # LTC и DOGE - это разные сети, поэтому у них разные network_hashrate
                        # Для DOGE используем актуальное значение network_hashrate из capminer.ru тестов
                        # DOGE network_hashrate: ~2,958,883 GH/s (не зависит от LTC network_hashrate)
                        doge_network_hashrate = 2_958_883  # GH/s - актуальное значение для DOGE из capminer.ru
                        coin_data_input["DOGE"] = {
                            "price": doge_coin.current_price_usd,
                            "network_hashrate": doge_network_hashrate,  # Отдельный network_hashrate для DOGE
                            "block_reward": 10000,  # Стандартный block_reward для DOGE
                            "algorithm": algorithm.value.lower(),
                        }
                        display_symbols.append("DOGE")

                result = MiningCalculator.calculate_profitability(
                    hash_rate=hashrate,
                    power_consumption=power,
                    electricity_price_rub=electricity_price,
                    coin_data=coin_data_input,
                    usd_to_rub=usd_to_rub,
                    algorithm=algorithm.value.lower()  # Передаем алгоритм
                )
                text = (
                    f"⚙️ **Алгоритм:** {algorithm.value}\n"
                )
                text += MiningCalculator.format_result(result, display_symbols, usd_to_rub)

            await message.answer(text, reply_markup=await CalculatorKB.result_menu())
            await state.set_state(CalculatorState.show_result)
        except Exception as e:
            print(f"Ошибка в calc_electricity_handler: {e}")
            import traceback
            traceback.print_exc()
            await message.answer(
                "❌ Произошла ошибка при расчете. Попробуйте еще раз.",
                reply_markup=await CalculatorKB.electricity_input(),
            )
        
    async def calc_power_handler(self, message: types.Message, state: FSMContext):
        # Проверка типа данных - только текстовые сообщения
        if not message.text:
            await message.answer(
                "❌ Пожалуйста, отправьте текстовое сообщение с потреблением (W).",
                reply_markup=await CalculatorKB.power_input(),
            )
            return
        
        try:
            power = float(message.text.replace(",", "."))
            if power <= 0:
                raise ValueError
        except ValueError:
            await message.answer(
                "❌ Введите положительное число:",
                reply_markup=await CalculatorKB.power_input(),
            )
            return

        await state.update_data(power=power)
        await message.answer(
            "💡 Введите стоимость электроэнергии (₽/кВт·ч):",
            reply_markup=await CalculatorKB.electricity_input(),
        )
        await state.set_state(CalculatorState.input_electricity_price)

    async def calc_usd_handler(self, call: types.CallbackQuery, state: FSMContext):
        data = await state.get_data()
        electricity_price = data["electricity_price"]

        coin_service = CoinGeckoService(self.settings)
        usd_to_rub = await coin_service.get_usd_rub_rate()

        if data.get("method") == "asic":
            # Загружаем модель заново из БД по model_id, так как объект ORM может быть неполным после сериализации
            model_id = data.get("model_id")
            if not model_id:
                await call.message.edit_text("❌ Ошибка: данные о модели не найдены. Пожалуйста, начните расчет заново.")
                return
            model = await self.calculator_req.get_asic_model_by_id(model_id)
            if not model:
                await call.message.edit_text("❌ Модель не найдена в базе данных")
                return
            model_line = await self.calculator_req.get_model_line_by_id(
                model.model_line_id
            )
            
            coin_data = {}
            coin_symbols = []

            if model.get_coin and model.get_coin.strip():
                # Оптимизация: загружаем все монеты одним запросом вместо цикла
                coin_symbols_list = [s.strip().upper() for s in model.get_coin.split(",")]
                # Для Scrypt сразу добавляем DOGE, если есть LTC
                if model_line.algorithm == Algorithm.SCRYPT and "LTC" in coin_symbols_list and "DOGE" not in coin_symbols_list:
                    coin_symbols_list.append("DOGE")
                
                coins_dict = await self.coin_req.get_coins_by_symbols(coin_symbols_list)
                
                # Загружаем данные алгоритмов одним запросом
                algorithms_set = {coin.algorithm for coin in coins_dict.values() if coin}
                algo_data_dict = await self.calculator_req.get_algorithm_data_batch(algorithms_set)
                
                # Формируем список монет с данными алгоритмов
                all_coins = []
                for coin_symbol in coin_symbols_list:
                    coin = coins_dict.get(coin_symbol)
                    if coin:
                        algo_data = algo_data_dict.get(coin.algorithm)
                        if algo_data:
                            all_coins.append({
                                "symbol": coin_symbol,
                                "coin": coin,
                                "algo_data": algo_data
                            })
                
                # Применяем фильтрацию монет согласно правилам
                filtered_coins = await self._filter_coins_for_miner(model_line, all_coins)
                
                # Формируем coin_data из отфильтрованных монет
                for coin_info in filtered_coins:
                    coin_symbol = coin_info["symbol"]
                    coin = coin_info["coin"]
                    algo_data = coin_info["algo_data"]
                    coin_data[coin_symbol] = {
                        "price": coin.current_price_usd,
                        "network_hashrate": algo_data.network_hashrate,
                        "block_reward": algo_data.block_reward,
                        "algorithm": coin.algorithm.value.lower(),
                    }
                    coin_symbols.append(coin_symbol)
                
                # Для Scrypt добавляем DOGE (если есть LTC) - DOGE уже загружен выше
                if model_line.algorithm == Algorithm.SCRYPT and "LTC" in [c["symbol"] for c in filtered_coins]:
                    doge_coin = coins_dict.get("DOGE")
                    if doge_coin and "DOGE" not in coin_data:
                        doge_network_hashrate = 2_958_883  # GH/s - актуальное значение для DOGE из capminer.ru
                        coin_data["DOGE"] = {
                            "price": doge_coin.current_price_usd,
                            "network_hashrate": doge_network_hashrate,
                            "block_reward": 10000,
                            "algorithm": model_line.algorithm.value.lower(),
                        }
                        coin_symbols.append("DOGE")
            else:
                algo_data = await self.calculator_req.get_algorithm_data(
                    model_line.algorithm
                )
                coin = await self.coin_req.get_coin_by_symbol(
                    algo_data.default_coin
                )
                if coin and algo_data:
                    coin_data[coin.symbol] = {
                        "price": coin.current_price_usd,
                        "network_hashrate": algo_data.network_hashrate,
                        "block_reward": algo_data.block_reward,
                        "algorithm": model_line.algorithm.value.lower(),
                    }
                    coin_symbols.append(coin.symbol)
                    
                    # Для Scrypt добавляем DOGE (если default_coin LTC)
                    if model_line.algorithm == Algorithm.SCRYPT and coin.symbol == "LTC":
                        doge_coin = await self.coin_req.get_coin_by_symbol("DOGE")
                        if doge_coin:
                            doge_network_hashrate = 2_958_883  # GH/s - актуальное значение для DOGE из capminer.ru
                            coin_data["DOGE"] = {
                                "price": doge_coin.current_price_usd,
                                "network_hashrate": doge_network_hashrate,
                                "block_reward": 10000,
                                "algorithm": model_line.algorithm.value.lower(),
                            }
                            coin_symbols.append("DOGE")

            if not coin_symbols:
                await call.message.edit_text("❌ Не удалось найти данные о монетах")
                return

            result = MiningCalculator.calculate_profitability(
                hash_rate=model.hash_rate,
                power_consumption=model.power_consumption,
                electricity_price_rub=electricity_price,
                coin_data=coin_data,
                usd_to_rub=usd_to_rub,
                algorithm=model_line.algorithm.value.lower(),
            )

            text = (
                f"🔧 **Оборудование:** {model_line.manufacturer.value} {model.name}\n"
            )
            text += MiningCalculator.format_result(result, coin_symbols, usd_to_rub)

        else:
            algorithm = data["algorithm"]
            hashrate = data["hashrate"]
            power = data["power"]

            algo_data = await self.calculator_req.get_algorithm_data(algorithm)
            coin = await self.coin_req.get_coin_by_symbol(algo_data.default_coin)

            # ВАЖНО: Для Etchash хэшрейт должен быть в GH/s (как на capminer.ru)
            # Если пользователь ввел значение, думая что это TH/s, нужно конвертировать
            algorithm_lower = algorithm.value.lower()
            # В базе данных ETCHASH определен как "Etchash/Ethash"
            hashrate_display = hashrate
            hashrate_unit_display = "TH/s"
            
            if algorithm_lower in ["etchash", "ethash", "etchash/ethash"]:
                # Если значение меньше 1, возможно пользователь ввел в TH/s (например, 0.5 TH/s = 500 GH/s)
                # Конвертируем из TH/s в GH/s
                if hashrate < 1:
                    hashrate = hashrate * 1000  # TH/s -> GH/s
                hashrate_unit_display = "GH/s"
                hashrate_display = hashrate
            elif algorithm_lower in ["scrypt", "blake2b+sha3", "blake2b_sha3"]:
                hashrate_unit_display = "GH/s"
            elif algorithm_lower in ["blake2s"]:
                hashrate_unit_display = "TH/s"  # Для Blake2S в TH/s
            elif algorithm_lower in ["kheavyhash"]:
                hashrate_unit_display = "TH/s"  # Для kHeavyHash в TH/s
            # Для SHA-256 остается TH/s

            # Формируем coin_data
            coin_data_input = {
                coin.symbol: {
                    "price": coin.current_price_usd,
                    "network_hashrate": algo_data.network_hashrate,
                    "block_reward": algo_data.block_reward,
                    "algorithm": algorithm.value.lower(),
                }
            }
            
            # Для Scrypt добавляем DOGE (если default_coin LTC)
            display_symbols = [coin.symbol]
            if algorithm == Algorithm.SCRYPT and coin.symbol == "LTC":
                doge_coin = await self.coin_req.get_coin_by_symbol("DOGE")
                if doge_coin:
                    # LTC и DOGE - это разные сети, поэтому у них разные network_hashrate
                    # Для DOGE используем актуальное значение network_hashrate из capminer.ru тестов
                    # DOGE network_hashrate: ~2,958,883 GH/s (не зависит от LTC network_hashrate)
                    doge_network_hashrate = 2_958_883  # GH/s - актуальное значение для DOGE из capminer.ru
                    coin_data_input["DOGE"] = {
                        "price": doge_coin.current_price_usd,
                        "network_hashrate": doge_network_hashrate,  # Отдельный network_hashrate для DOGE
                        "block_reward": 10000,  # Стандартный block_reward для DOGE
                        "algorithm": algorithm.value.lower(),
                    }
                    display_symbols.append("DOGE")

            result = MiningCalculator.calculate_profitability(
                hash_rate=hashrate,
                power_consumption=power,
                electricity_price_rub=electricity_price,
                coin_data=coin_data_input,
                usd_to_rub=usd_to_rub,
                algorithm=algorithm.value.lower()  # Передаем алгоритм
            )

            text = (
                f"⚙️ **Алгоритм:** {algorithm.value}\n"
                f"⚡ **Хэшрейт:** {hashrate_display} {hashrate_unit_display}\n"
                f"🔌 **Мощность:** {power}W\n\n"
            )
            text += MiningCalculator.format_result(result, display_symbols, usd_to_rub)

        await call.message.edit_text(text, reply_markup=await CalculatorKB.result_menu())

    async def back_chars_lines_handler(
        self, call: types.CallbackQuery, state: FSMContext
    ):
        try:
            data = await state.get_data()
            manufacturer = data["manufacturer"]

            model_lines = await self.calculator_req.get_model_lines_by_manufacturer(
                manufacturer
            )

            await call.message.edit_text(
                f"📱 Выберите модельную линейку {manufacturer.value}:",
                reply_markup=await ClientKB.chars_model_lines(model_lines),
            )
        except TelegramBadRequest as e:
            if "message is not modified" not in str(e):
                raise
        finally:
            try:
                await call.answer()
            except TelegramBadRequest:
                pass

    async def calc_rub_handler(self, call: types.CallbackQuery, state: FSMContext):
        data = await state.get_data()
        electricity_price = data["electricity_price"]

        coin_service = CoinGeckoService(self.settings)
        usd_to_rub = await coin_service.get_usd_rub_rate()

        if data.get("method") == "asic":
            # Загружаем модель заново из БД по model_id, так как объект ORM может быть неполным после сериализации
            model_id = data.get("model_id")
            if not model_id:
                await call.message.edit_text("❌ Ошибка: данные о модели не найдены. Пожалуйста, начните расчет заново.")
                return
            model = await self.calculator_req.get_asic_model_by_id(model_id)
            if not model:
                await call.message.edit_text("❌ Модель не найдена в базе данных")
                return
            model_line = await self.calculator_req.get_model_line_by_id(
                model.model_line_id
            )
            
            coin_data = {}
            coin_symbols = []

            if model.get_coin and model.get_coin.strip():
                # Оптимизация: загружаем все монеты одним запросом вместо цикла
                coin_symbols_list = [s.strip().upper() for s in model.get_coin.split(",")]
                # Для Scrypt сразу добавляем DOGE, если есть LTC
                if model_line.algorithm == Algorithm.SCRYPT and "LTC" in coin_symbols_list and "DOGE" not in coin_symbols_list:
                    coin_symbols_list.append("DOGE")
                
                coins_dict = await self.coin_req.get_coins_by_symbols(coin_symbols_list)
                
                # Загружаем данные алгоритмов одним запросом
                algorithms_set = {coin.algorithm for coin in coins_dict.values() if coin}
                algo_data_dict = await self.calculator_req.get_algorithm_data_batch(algorithms_set)
                
                # Формируем список монет с данными алгоритмов
                all_coins = []
                for coin_symbol in coin_symbols_list:
                    coin = coins_dict.get(coin_symbol)
                    if coin:
                        algo_data = algo_data_dict.get(coin.algorithm)
                        if algo_data:
                            all_coins.append({
                                "symbol": coin_symbol,
                                "coin": coin,
                                "algo_data": algo_data
                            })
                
                # Применяем фильтрацию монет согласно правилам
                filtered_coins = await self._filter_coins_for_miner(model_line, all_coins)
                
                # Формируем coin_data из отфильтрованных монет
                for coin_info in filtered_coins:
                    coin_symbol = coin_info["symbol"]
                    coin = coin_info["coin"]
                    algo_data = coin_info["algo_data"]
                    coin_data[coin_symbol] = {
                        "price": coin.current_price_usd,
                        "network_hashrate": algo_data.network_hashrate,
                        "block_reward": algo_data.block_reward,
                        "algorithm": coin.algorithm.value.lower(),
                    }
                    coin_symbols.append(coin_symbol)
                
                # Для Scrypt добавляем DOGE (если есть LTC) - DOGE уже загружен выше
                if model_line.algorithm == Algorithm.SCRYPT and "LTC" in [c["symbol"] for c in filtered_coins]:
                    doge_coin = coins_dict.get("DOGE")
                    if doge_coin and "DOGE" not in coin_data:
                        doge_network_hashrate = 2_958_883  # GH/s - актуальное значение для DOGE из capminer.ru
                        coin_data["DOGE"] = {
                            "price": doge_coin.current_price_usd,
                            "network_hashrate": doge_network_hashrate,
                            "block_reward": 10000,
                            "algorithm": model_line.algorithm.value.lower(),
                        }
                        coin_symbols.append("DOGE")
            else:
                algo_data = await self.calculator_req.get_algorithm_data(
                    model_line.algorithm
                )
                coin = await self.coin_req.get_coin_by_symbol(
                    algo_data.default_coin
                )
                if coin and algo_data:
                    coin_data[coin.symbol] = {
                        "price": coin.current_price_usd,
                        "network_hashrate": algo_data.network_hashrate,
                        "block_reward": algo_data.block_reward,
                        "algorithm": model_line.algorithm.value.lower(),
                    }
                    coin_symbols.append(coin.symbol)
                    
                    # Для Scrypt добавляем DOGE (если default_coin LTC)
                    if model_line.algorithm == Algorithm.SCRYPT and coin.symbol == "LTC":
                        doge_coin = await self.coin_req.get_coin_by_symbol("DOGE")
                        if doge_coin:
                            doge_network_hashrate = 2_958_883  # GH/s - актуальное значение для DOGE из capminer.ru
                            coin_data["DOGE"] = {
                                "price": doge_coin.current_price_usd,
                                "network_hashrate": doge_network_hashrate,
                                "block_reward": 10000,
                                "algorithm": model_line.algorithm.value.lower(),
                            }
                            coin_symbols.append("DOGE")

            result = MiningCalculator.calculate_profitability(
                hash_rate=model.hash_rate,
                power_consumption=model.power_consumption,
                electricity_price_rub=electricity_price,
                coin_data=coin_data,
                usd_to_rub=usd_to_rub,
                algorithm=model_line.algorithm.value.lower(),
            )

            text = (
                f"🔧 **Оборудование:** {model_line.manufacturer.value} {model.name}\n"
            )
            text += MiningCalculator.format_result_rub(
                result, coin_symbols, usd_to_rub
            )

        else:
            algorithm = data["algorithm"]
            hashrate = data["hashrate"]
            power = data["power"]

            algo_data = await self.calculator_req.get_algorithm_data(algorithm)
            coin = await self.coin_req.get_coin_by_symbol(algo_data.default_coin)

            # ВАЖНО: Для Etchash хэшрейт должен быть в GH/s (как на capminer.ru)
            # Если пользователь ввел значение, думая что это TH/s, нужно конвертировать
            algorithm_lower = algorithm.value.lower()
            hashrate_display = hashrate
            hashrate_unit_display = "TH/s"
            
            # В базе данных ETCHASH определен как "Etchash/Ethash"
            if algorithm_lower in ["etchash", "ethash", "etchash/ethash"]:
                # Если значение меньше 1, возможно пользователь ввел в TH/s (например, 0.5 TH/s = 500 GH/s)
                # Конвертируем из TH/s в GH/s
                if hashrate < 1:
                    hashrate = hashrate * 1000  # TH/s -> GH/s
                hashrate_unit_display = "GH/s"
                hashrate_display = hashrate
            elif algorithm_lower in ["scrypt", "blake2b+sha3", "blake2b_sha3"]:
                hashrate_unit_display = "GH/s"
            elif algorithm_lower in ["blake2s"]:
                hashrate_unit_display = "TH/s"  # Для Blake2S в TH/s
            elif algorithm_lower in ["kheavyhash"]:
                hashrate_unit_display = "TH/s"  # Для kHeavyHash в TH/s
            # Для SHA-256 остается TH/s

            # Формируем coin_data
            coin_data_input = {
                coin.symbol: {
                    "price": coin.current_price_usd,
                    "network_hashrate": algo_data.network_hashrate,
                    "block_reward": algo_data.block_reward,
                    "algorithm": algorithm.value.lower(),
                }
            }
            
            # Для Scrypt добавляем DOGE (если default_coin LTC)
            display_symbols = [coin.symbol]
            if algorithm == Algorithm.SCRYPT and coin.symbol == "LTC":
                doge_coin = await self.coin_req.get_coin_by_symbol("DOGE")
                if doge_coin:
                    # LTC и DOGE - это разные сети, поэтому у них разные network_hashrate
                    # Для DOGE используем актуальное значение network_hashrate из capminer.ru тестов
                    # DOGE network_hashrate: ~2,958,883 GH/s (не зависит от LTC network_hashrate)
                    doge_network_hashrate = 2_958_883  # GH/s - актуальное значение для DOGE из capminer.ru
                    coin_data_input["DOGE"] = {
                        "price": doge_coin.current_price_usd,
                        "network_hashrate": doge_network_hashrate,  # Отдельный network_hashrate для DOGE
                        "block_reward": 10000,  # Стандартный block_reward для DOGE
                        "algorithm": algorithm.value.lower(),
                    }
                    display_symbols.append("DOGE")

            result = MiningCalculator.calculate_profitability(
                hash_rate=hashrate,
                power_consumption=power,
                electricity_price_rub=electricity_price,
                coin_data=coin_data_input,
                usd_to_rub=usd_to_rub,
                algorithm=algorithm.value.lower()  # Передаем алгоритм
            )

            text = (
                f"⚙️ **Алгоритм:** {algorithm.value}\n"
                f"⚡ **Хэшрейт:** {hashrate_display} {hashrate_unit_display}\n"
                f"🔌 **Мощность:** {power}W\n\n"
            )
            text += MiningCalculator.format_result_rub(
                result, display_symbols, usd_to_rub
            )

        await call.message.edit_text(
            text, reply_markup=await CalculatorKB.result_menu_rub()
        )

    async def back_calc_manufacturer_handler(
        self, call: types.CallbackQuery, state: FSMContext
    ):
        await call.message.edit_text(
            "⚙️ Выберите способ расчета:",
            reply_markup=await CalculatorKB.choose_method(),
        )
        try:
            await call.answer()
        except TelegramBadRequest:
            pass

    async def back_calc_line_handler(
        self, call: types.CallbackQuery, state: FSMContext
    ):
        data = await state.get_data()
        manufacturer = data["manufacturer"]
        model_lines = await self.calculator_req.get_model_lines_by_manufacturer(
            manufacturer
        )
        await call.message.edit_text(
            f"📱 Выберите модельную линейку {manufacturer.value}:",
            reply_markup=await CalculatorKB.choose_model_lines(model_lines, page=0),
        )
        try:
            await call.answer()
        except TelegramBadRequest:
            pass

    async def back_calc_model_handler(
        self, call: types.CallbackQuery, state: FSMContext
    ):
        data = await state.get_data()
        manufacturer = data["manufacturer"]
        model_line = data["model_line"]
        models = await self.calculator_req.get_asic_models_by_model_line(model_line.id)
        await call.message.edit_text(
            f"🔧 Выберите модель {model_line.manufacturer.value} {model_line.name}:",
            reply_markup=await CalculatorKB.choose_asic_models_by_line(
                models, model_line.name, page=0
            ),
        )
        try:
            await call.answer()
        except TelegramBadRequest:
            pass

    async def back_calc_algorithm_handler(
        self, call: types.CallbackQuery, state: FSMContext
    ):
        await call.message.edit_text(
            "⚙️ Выберите алгоритм:",
            reply_markup=await CalculatorKB.choose_algorithm(),
        )
        try:
            await call.answer()
        except TelegramBadRequest:
            pass

    async def calc_hashrate_handler(self, message: types.Message, state: FSMContext):
        # Проверка типа данных - только текстовые сообщения
        if not message.text:
            data = await state.get_data()
            algorithm = data.get("algorithm")
            hashrate_unit = "TH/s"  # По умолчанию
            
            if algorithm:
                algorithm_lower = algorithm.value.lower()
                if algorithm_lower in ["sha-256", "sha256"]:
                    hashrate_unit = "TH/s"
                elif algorithm_lower in ["scrypt", "etchash", "ethash", "etchash/ethash", "blake2b+sha3", "blake2b_sha3"]:
                    hashrate_unit = "GH/s"
                elif algorithm_lower in ["blake2s"]:
                    hashrate_unit = "TH/s"
                elif algorithm_lower in ["kheavyhash"]:
                    hashrate_unit = "TH/s"
            
            await message.answer(
                f"❌ Пожалуйста, отправьте текстовое сообщение с хешрейтом ({hashrate_unit}).",
                reply_markup=await CalculatorKB.hashrate_input(),
            )
            return
        
        try:
            hashrate = float(message.text.replace(",", "."))
            if hashrate <= 0:
                raise ValueError
        except ValueError:
            # Определяем единицы измерения для сообщения об ошибке
            data = await state.get_data()
            algorithm = data.get("algorithm")
            hashrate_unit = "TH/s"  # По умолчанию
            
            if algorithm:
                algorithm_lower = algorithm.value.lower()
                # В базе данных ETCHASH определен как "Etchash/Ethash"
                if algorithm_lower in ["sha-256", "sha256"]:
                    hashrate_unit = "TH/s"
                elif algorithm_lower in ["scrypt", "etchash", "ethash", "etchash/ethash", "blake2b+sha3", "blake2b_sha3"]:
                    hashrate_unit = "GH/s"
                elif algorithm_lower in ["blake2s"]:
                    hashrate_unit = "TH/s"  # Для Blake2S в TH/s
                elif algorithm_lower in ["kheavyhash"]:
                    hashrate_unit = "TH/s"  # Для kHeavyHash в TH/s
            
            await message.answer(
                f"❌ Введите положительное число ({hashrate_unit}):",
                reply_markup=await CalculatorKB.hashrate_input(),
            )
            return

        await state.update_data(hashrate=hashrate)
        await message.answer(
            "⚡ Введите потребление (W):",
            reply_markup=await CalculatorKB.power_input(),
        )
        await state.set_state(CalculatorState.input_power)

    async def back_calc_hashrate_handler(
        self, call: types.CallbackQuery, state: FSMContext
    ):
        data = await state.get_data()
        algorithm = data.get("algorithm")
        
        # Определяем единицы измерения хэшрейта для каждого алгоритма
        if algorithm:
            algorithm_lower = algorithm.value.lower()
            # В базе данных ETCHASH определен как "Etchash/Ethash"
            if algorithm_lower in ["sha-256", "sha256"]:
                hashrate_unit = "TH/s"
            elif algorithm_lower in ["scrypt"]:
                hashrate_unit = "GH/s"
            elif algorithm_lower in ["etchash", "ethash", "etchash/ethash"]:
                hashrate_unit = "GH/s"  # Для Etchash вводим в GH/s
            elif algorithm_lower in ["kheavyhash"]:
                hashrate_unit = "TH/s"  # Для kHeavyHash в TH/s
            elif algorithm_lower in ["blake2s"]:
                hashrate_unit = "TH/s"  # Для Blake2S в TH/s
            elif algorithm_lower in ["blake2b+sha3", "blake2b_sha3"]:
                hashrate_unit = "GH/s"
            else:
                hashrate_unit = "TH/s"  # По умолчанию
        else:
            hashrate_unit = "TH/s"
        
        await call.message.edit_text(
            f"⚡ Введите ваш хешрейт ({hashrate_unit}):",
            reply_markup=await CalculatorKB.hashrate_input(),
        )
        await state.set_state(CalculatorState.input_hashrate)
        try:
            await call.answer()
        except TelegramBadRequest:
            pass

    async def sell_start_handler(self, message: types.Message, state: FSMContext):
        await message.answer("📱 Введите модель устройства, которое хотите продать:")
        await state.set_state(SellForm.device)

    async def sell_start_handler_call(
        self, call: types.CallbackQuery, state: FSMContext
    ):
        await call.message.answer(
            "📱 Введите модель устройства, которое хотите продать:"
        )
        await state.set_state(SellForm.device)

    async def sell_device_handler(self, message: types.Message, state: FSMContext):
        # Проверка типа данных - только текстовые сообщения
        if not message.text:
            await message.answer("❌ Пожалуйста, отправьте текстовое сообщение с моделью устройства.")
            return
        
        # Проверка на пустое сообщение
        device_text = message.text.strip()
        if not device_text:
            await message.answer("❌ Модель устройства не может быть пустой. Введите модель устройства:")
            return
        
        # Проверка минимальной длины (должно быть хотя бы 2 символа)
        if len(device_text) < 2:
            await message.answer("❌ Модель устройства слишком короткая (минимум 2 символа). Введите модель устройства:")
            return
        
        # Проверка длины (разумный лимит)
        if len(device_text) > 200:
            await message.answer("❌ Модель устройства слишком длинная (максимум 200 символов). Введите короче:")
            return
        
        # Проверка на валидность: подсчитываем количество букв и цифр
        alnum_count = sum(1 for c in device_text if c.isalnum())
        total_length = len(device_text)
        
        # Должно быть хотя бы 50% букв/цифр (или минимум 2 символа для коротких строк)
        min_alnum = max(2, total_length // 2)
        if alnum_count < min_alnum:
            await message.answer(
                f"❌ Модель устройства содержит слишком много специальных символов. "
                f"Введите корректную модель устройства (буквы, цифры, дефисы, пробелы)."
            )
            return
        
        await state.update_data(device=device_text)
        await message.answer("💰 Введите цену продажи (в рублях):")
        await state.set_state(SellForm.price)

    async def sell_price_handler(self, message: types.Message, state: FSMContext):
        # Проверка типа данных - только текстовые сообщения
        if not message.text:
            await message.answer("❌ Пожалуйста, отправьте текстовое сообщение с ценой.")
            return
        
        # Проверка на пустое сообщение
        price_text = message.text.strip().replace(" ", "").replace(",", ".")
        if not price_text:
            await message.answer("❌ Цена не может быть пустой. Введите цену продажи (в рублях):")
            return
        
        # Проверка, что это число (целое или десятичное)
        try:
            price = float(price_text)
            if price <= 0:
                await message.answer("❌ Цена должна быть больше нуля. Введите корректную цену (например: 50000 или 50000.50):")
                return
            if price > 1e9:  # Проверка на разумный максимум (1 миллиард)
                await message.answer("❌ Цена слишком большая. Введите корректную цену (максимум 1 000 000 000):")
                return
        except ValueError:
            await message.answer("❌ Введите корректную цену (число, например: 50000 или 50000.50):")
            return

        await state.update_data(price=price)
        await message.answer(
            "📝 Опишите состояние устройства (новое/б/у, год покупки и т.д.):"
        )
        await state.set_state(SellForm.condition)

    async def sell_condition_handler(self, message: types.Message, state: FSMContext):
        # Проверка типа данных - только текстовые сообщения
        if not message.text:
            await message.answer("❌ Пожалуйста, отправьте текстовое сообщение с описанием состояния.")
            return
        
        # Проверка на пустое сообщение
        condition_text = message.text.strip()
        if not condition_text:
            await message.answer("❌ Описание состояния не может быть пустым. Опишите состояние устройства:")
            return
        
        # Проверка минимальной длины
        if len(condition_text) < 3:
            await message.answer("❌ Описание состояния слишком короткое (минимум 3 символа). Опишите состояние устройства:")
            return
        
        # Проверка длины (разумный лимит)
        if len(condition_text) > 500:
            await message.answer("❌ Описание состояния слишком длинное (максимум 500 символов). Введите короче:")
            return
        
        # Проверка на валидность: подсчитываем количество букв и цифр
        alnum_count = sum(1 for c in condition_text if c.isalnum())
        total_length = len(condition_text)
        
        # Должно быть хотя бы 40% букв/цифр (или минимум 3 символа для коротких строк)
        min_alnum = max(3, total_length * 2 // 5)
        if alnum_count < min_alnum:
            await message.answer(
                f"❌ Описание состояния содержит слишком много специальных символов. "
                f"Опишите состояние устройства на русском или английском языке."
            )
            return
        
        await state.update_data(condition=condition_text)
        await message.answer("📋 Добавьте описание (комплектация, особенности и т.д.):")
        await state.set_state(SellForm.description)

    async def sell_description_handler(self, message: types.Message, state: FSMContext):
        # Проверка типа данных - только текстовые сообщения
        if not message.text:
            await message.answer("❌ Пожалуйста, отправьте текстовое сообщение с описанием.")
            return
        
        # Проверка на пустое сообщение
        description_text = message.text.strip()
        if not description_text:
            await message.answer("❌ Описание не может быть пустым. Добавьте описание:")
            return
        
        # Проверка минимальной длины
        if len(description_text) < 3:
            await message.answer("❌ Описание слишком короткое (минимум 3 символа). Добавьте описание:")
            return
        
        # Проверка длины (разумный лимит)
        if len(description_text) > 1000:
            await message.answer("❌ Описание слишком длинное (максимум 1000 символов). Введите короче:")
            return
        
        # Проверка на валидность: подсчитываем количество букв и цифр
        alnum_count = sum(1 for c in description_text if c.isalnum())
        total_length = len(description_text)
        
        # Должно быть хотя бы 40% букв/цифр (или минимум 3 символа для коротких строк)
        min_alnum = max(3, total_length * 2 // 5)
        if alnum_count < min_alnum:
            await message.answer(
                f"❌ Описание содержит слишком много специальных символов. "
                f"Добавьте описание на русском или английском языке."
            )
            return
        
        await state.update_data(description=description_text)
        await message.answer(
            "📞 Укажите контакты для связи (телефон, Telegram и т.д.):"
        )
        await state.set_state(SellForm.contact)

    async def sell_contact_handler(self, message: types.Message, state: FSMContext):
        # Проверка типа данных - только текстовые сообщения
        if not message.text:
            await message.answer("❌ Пожалуйста, отправьте текстовое сообщение с контактами.")
            return
        
        # Проверка на пустое сообщение
        contact_text = message.text.strip()
        if not contact_text:
            await message.answer("❌ Контакты не могут быть пустыми. Укажите контакты для связи:")
            return
        
        # Проверка минимальной длины
        if len(contact_text) < 3:
            await message.answer("❌ Контакты слишком короткие (минимум 3 символа). Укажите контакты для связи:")
            return
        
        # Проверка длины (разумный лимит)
        if len(contact_text) > 200:
            await message.answer("❌ Контакты слишком длинные (максимум 200 символов). Введите короче:")
            return
        
        # Проверка на валидность: подсчитываем количество букв и цифр
        alnum_count = sum(1 for c in contact_text if c.isalnum())
        total_length = len(contact_text)
        
        # Должно быть хотя бы 50% букв/цифр (или минимум 2 символа для коротких строк)
        min_alnum = max(2, total_length // 2)
        if alnum_count < min_alnum:
            await message.answer(
                f"❌ Контакты содержат слишком много специальных символов. "
                f"Укажите корректные контакты (телефон, Telegram, email и т.д.)."
            )
            return
        
        await state.update_data(contact=contact_text)
        data = await state.get_data()
        
        # Дополнительная проверка всех данных перед отправкой
        if not data.get("device") or not data.get("price") or not data.get("condition") or not data.get("description") or not data.get("contact"):
            await message.answer("❌ Ошибка: не все данные заполнены. Пожалуйста, начните заново.")
            await state.clear()
            return

        def escape_html(text):
            if not text:
                return ""
            return (
                str(text)
                .replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
                .replace('"', "&quot;")
            )

        # Финальная проверка валидности всех данных перед отправкой
        device = data.get("device", "").strip()
        price = data.get("price", 0)
        condition = data.get("condition", "").strip()
        description = data.get("description", "").strip()
        contact = data.get("contact", "").strip()
        
        # Проверка, что все поля заполнены и валидны
        validation_errors = []
        if not device or len(device) < 2:
            validation_errors.append("модель устройства")
        else:
            alnum_count = sum(1 for c in device if c.isalnum())
            if alnum_count < max(2, len(device) // 2):
                validation_errors.append("модель устройства")
        if not price or not isinstance(price, (int, float)) or price <= 0:
            validation_errors.append("цена")
        if not condition or len(condition) < 3:
            validation_errors.append("состояние устройства")
        else:
            alnum_count = sum(1 for c in condition if c.isalnum())
            if alnum_count < max(3, len(condition) * 2 // 5):
                validation_errors.append("состояние устройства")
        if not description or len(description) < 3:
            validation_errors.append("описание")
        else:
            alnum_count = sum(1 for c in description if c.isalnum())
            if alnum_count < max(3, len(description) * 2 // 5):
                validation_errors.append("описание")
        if not contact or len(contact) < 3:
            validation_errors.append("контакты")
        else:
            alnum_count = sum(1 for c in contact if c.isalnum())
            if alnum_count < max(2, len(contact) // 2):
                validation_errors.append("контакты")
        
        if validation_errors:
            await message.answer(
                f"❌ Ошибка валидации: некорректно заполнены поля: {', '.join(validation_errors)}. "
                f"Пожалуйста, начните заново."
            )
            await state.clear()
            return
        
        try:
            escaped_device = escape_html(device)
            # Форматируем цену: если целое число, показываем без десятичных, иначе с 2 знаками
            if isinstance(price, float) and price.is_integer():
                price_str = str(int(price))
            else:
                price_str = f"{price:.2f}".rstrip('0').rstrip('.')
            escaped_price = escape_html(price_str)
            escaped_condition = escape_html(condition)
            escaped_description = escape_html(description)
            escaped_contact = escape_html(contact)
            escaped_username = escape_html(
                message.from_user.username or message.from_user.first_name
            )

            await self.bot.send_message(
                chat_id=ADMIN_ID,
                text=(
                    f"📦 <b>Новая заявка на продажу</b>\n\n"
                    f"👤 От: @{escaped_username}\n"
                    f"ID: <code>{message.from_user.id}</code>\n\n"
                    f"📱 <b>Устройство:</b> {escaped_device}\n"
                    f"💰 <b>Цена:</b> {escaped_price} ₽\n"
                    f"🔧 <b>Состояние:</b> {escaped_condition}\n"
                    f"📋 <b>Описание:</b> {escaped_description}\n"
                    f"📞 <b>Контакты:</b> {escaped_contact}\n\n"
                    f"С вами скоро свяжется менеджер @snooby37."
                ),
                parse_mode="HTML",
            )
        except Exception as e:
            print(f"Ошибка при отправке заявки администратору (ID: {ADMIN_ID}): {e}")
            await message.answer(
                f"❌ Не удалось отправить заявку администратору. "
                f"Пожалуйста, свяжитесь с менеджером напрямую: @snooby37"
            )
            await state.clear()
            return

        await message.answer(
            "✅ Спасибо! С вами скоро свяжется менеджер @snooby37.", parse_mode=None
        )
        await state.clear()

    async def sell_invalid_content_handler(self, message: types.Message, state: FSMContext):
        """Обработчик для не-текстовых сообщений в форме продажи оборудования"""
        current_state = await state.get_state()
        
        if current_state == SellForm.device.state:
            await message.answer("❌ Пожалуйста, отправьте текстовое сообщение с моделью устройства.")
        elif current_state == SellForm.price.state:
            await message.answer("❌ Пожалуйста, отправьте текстовое сообщение с ценой.")
        elif current_state == SellForm.condition.state:
            await message.answer("❌ Пожалуйста, отправьте текстовое сообщение с описанием состояния.")
        elif current_state == SellForm.description.state:
            await message.answer("❌ Пожалуйста, отправьте текстовое сообщение с описанием.")
        elif current_state == SellForm.contact.state:
            await message.answer("❌ Пожалуйста, отправьте текстовое сообщение с контактами.")