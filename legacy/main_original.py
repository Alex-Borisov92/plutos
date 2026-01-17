import time
import numpy as np
import mss
import concurrent.futures
import logging
import tkinter as tk
from tkinter import messagebox
from PIL import Image
import pytesseract
import cv2
import re
import os
from treys import Evaluator, Card, Deck
import random

# Укажите путь к tesseract.exe, если он установлен не по умолчанию
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
RESULT = {}
# =========================
# Настройки для определения позиции и pot
# =========================

# Координаты пикселей для определения дилера (примерные значения, замените на ваши)
PIXEL_DEALER_COORDS = [  # тест на видео
    # {'left': 482,   'top': 148}, 
    {'left': -1101, 'top': 687}, 
    {'left': -836,  'top': 686}, 
    {'left': -593,  'top': 870}, 
    {'left': -614,  'top': 1104},
    {'left': -932,  'top': 1180},
    {'left': -1234, 'top': 1185},
    {'left': -1324, 'top': 1104},
    {'left': -1345, 'top': 872},
]

# Координаты пикселей для определения активных игроков
PIXEL_INGAME_COORDS_R = [
    {'left': -1180, 'top': 633  , 'r':37}, 
    {'left': -690,  'top': 631  , 'r':40}, 
    {'left': -458,  'top': 809  , 'r':40}, 
    {'left': -475,  'top': 1035 , 'r':44},
    # {'left': -932,  'top': 1180 , 'r':}, # моя позиция, проверять не нужно 
    {'left': -1090, 'top': 1130 , 'r':43},
    {'left': -1403, 'top': 1045 , 'r':38},
    {'left': -1418, 'top': 803  , 'r':42},
]

# Координаты области для определения pot (суммы в банке)
POT_REGION = {'left': -1021, 'top': 720, 'width': 130, 'height': 35}

# Координаты области для определения ваших карт
CARD_REGION = {'left': -870, 'top': 1081, 'width': 62, 'height': 75}

# Индексы сидений, которые нужно проверять для активных игроков (исключая ваше сидение - Seat 5, индекс 4)
SEAT_INDICES_TO_CHECK = [0, 1, 2, 3, 5, 6, 7]

# Ваше место фиксировано на Seat 5 (индекс 4)
YOUR_SEAT_INDEX = 4  # Индекс от 0 до 7

# Определение позиций относительно дилера для 8 игроков
POSITIONS = ['Dealer', 'SB', 'BB', 'UTG', 'UTG+1', 'HJ', 'CO', 'BTN']

# =========================
# Диапазоны рук для каждой позиции (расширенные для микролимитов)
# =========================
position_ranges = {
    'Dealer': ['AA', 'KK', 'QQ', 'JJ', 'TT', '99', '88', '77', '66', '55', '44', '33', '22',
               'AKs', 'AQs', 'AJs', 'ATs', 'A9s', 'KQs', 'KJs', 'QJs', 'JTs',
               'AKo', 'AQo', 'AJo', 'ATo', 'KQo', 'QJo', 'JTo'],
    'SB': ['AA', 'KK', 'QQ', 'JJ', 'TT', '99', '88', '77', '66', '55', '44', '33', '22',
           'AKs', 'AQs', 'AJs', 'ATs', 'A9s', 'A8s', 'KQs', 'KJs', 'KTs', 'QJs', 'QTs', 'JTs', 'T9s',
           'AKo', 'AQo', 'AJo', 'ATo', 'A9o', 'A8o', 'KQo', 'QJo', 'JTo', 'T9o'],
    'BB': ['AA', 'KK', 'QQ', 'JJ', 'TT', '99', '88', '77', '66', '55', '44', '33', '22',
           'AKs', 'AQs', 'AJs', 'ATs', 'A9s', 'A8s', 'A7s', 'A6s', 'A5s', 'A4s', 'A3s', 'A2s',
           'KQs', 'KJs', 'KTs', 'K9s', 'K8s', 'K7s', 'QJs', 'QTs', 'Q9s', 'Q8s',
           'JTs', 'J9s', 'J8s', 'T9s', 'T8s', '98s', '97s', '87s', '76s', '65s', '54s',
           'AKo', 'AQo', 'AJo', 'ATo', 'A9o', 'A8o', 'A7o', 'A6o', 'A5o', 'A4o', 'A3o', 'A2o',
           'KQo', 'KJo', 'KTo', 'K9o', 'QJo', 'QTo', 'Q9o', 'JTo', 'J9o', 'T9o', '98o', '87o', '76o', '65o', '54o'],
    'UTG': ['AA', 'KK', 'QQ', 'JJ', 'TT', '99', '88', '77', '66', '55', '44', '33', '22',
            'AKs', 'AQs', 'AJs', 'ATs', 'A9s', 'KQs', 'KJs', 'QJs', 'JTs',
            'AKo', 'AQo', 'AJo', 'ATo', 'KQo', 'QJo', 'JTo'],
    'UTG+1': ['AA', 'KK', 'QQ', 'JJ', 'TT', '99', '88', '77', '66', '55', '44', '33', '22',
              'AKs', 'AQs', 'AJs', 'ATs', 'A9s', 'A8s', 'KQs', 'KJs', 'KTs', 'QJs', 'QTs', 'JTs', 'T9s',
              'AKo', 'AQo', 'AJo', 'ATo', 'A9o', 'A8o', 'KQo', 'QJo', 'JTo', 'T9o'],
    'HJ': ['AA', 'KK', 'QQ', 'JJ', 'TT', '99', '88', '77', '66', '55', '44', '33', '22',
           'AKs', 'AQs', 'AJs', 'ATs', 'A9s', 'A8s', 'A7s', 'KQs', 'KJs', 'KTs', 'QJs', 'QTs', 'JTs', 'T9s', '98s',
           'AKo', 'AQo', 'AJo', 'ATo', 'A9o', 'A8o', 'A7o', 'A6o', 'A5o', 'A4o', 'A3o', 'A2o',
           'KQo', 'QJo', 'JTo'],
    'CO': ['AA', 'KK', 'QQ', 'JJ', 'TT', '99', '88', '77', '66', '55', '44', '33', '22',
           'AKs', 'AQs', 'AJs', 'ATs', 'A9s', 'A8s', 'A7s', 'A6s', 'A5s', 'A4s', 'A3s', 'A2s',
           'KQs', 'KJs', 'KTs', 'K9s', 'K8s', 'K7s', 'QJs', 'QTs', 'Q9s', 'Q8s',
           'JTs', 'J9s', 'J8s', 'T9s', 'T8s', '98s', '97s', '87s', '76s', '65s', '54s',
           'AKo', 'AQo', 'AJo', 'ATo', 'A9o', 'A8o', 'A7o', 'A6o', 'A5o', 'A4o', 'A3o', 'A2o',
           'KQo', 'KJo', 'KTo', 'K9o', 'QJo', 'QTo', 'Q9o', 'JTo', 'J9o', 'T9o', '98o', '87o', '76o', '65o', '54o'],
    'BTN': ['AA', 'KK', 'QQ', 'JJ', 'TT', '99', '88', '77', '66', '55', '44', '33', '22',
            'AKs', 'AQs', 'AJs', 'ATs', 'A9s', 'A8s', 'A7s', 'A6s', 'A5s', 'A4s', 'A3s', 'A2s',
            'KQs', 'KJs', 'KTs', 'K9s', 'K8s', 'K7s', 'QJs', 'QTs', 'Q9s', 'Q8s',
            'JTs', 'J9s', 'J8s', 'T9s', 'T8s', '98s', '87s', '76s', '65s', '54s',
            'AKo', 'AQo', 'AJo', 'ATo', 'A9o', 'A8o', 'A7o', 'A6o', 'A5o', 'A4o', 'A3o', 'A2o',
            'KQo', 'KJo', 'KTo', 'K9o', 'QJo', 'QTo', 'Q9o', 'JTo', 'J9o', 'T9o', '98o', '87o', '76o', '65o', '54o']
}

# =========================
# Настройки для распознавания карт
# =========================

# Координаты областей для определения ваших карт в руке
HAND_CARD1_NUMBER_REGION = {'left': -860, 'top': 1090, 'width': 28, 'height': 43}
HAND_CARD2_NUMBER_REGION = {'left': -828, 'top': 1090, 'width': 28, 'height': 43}

HAND_CARD1_SUIT_REGION = {'left': -859, 'top': 1132, 'width': 17, 'height': 24}
HAND_CARD2_SUIT_REGION = {'left': -828, 'top': 1132, 'width': 17, 'height': 24}

STREET_CARD1_NUMBER_REGION = {'left': -1172,    'top': 854, 'width': 30,   'height': 44}
STREET_CARD2_NUMBER_REGION = {'left': -1087,    'top': 854, 'width': 30,   'height': 44}
STREET_CARD3_NUMBER_REGION = {'left': -999,     'top': 854, 'width': 30,   'height': 44}
STREET_CARD4_NUMBER_REGION = {'left': -915,     'top': 854, 'width': 30,   'height': 44}
STREET_CARD5_NUMBER_REGION = {'left': -829,     'top': 854, 'width': 30,   'height': 44}

STREET_CARD1_SUIT_REGION = {'left': -1172, 'top': 895, 'width': 17, 'height': 24}
STREET_CARD2_SUIT_REGION = {'left': -1087, 'top': 895, 'width': 17, 'height': 24}
STREET_CARD3_SUIT_REGION = {'left': -1001, 'top': 895, 'width': 17, 'height': 24}
STREET_CARD4_SUIT_REGION = {'left': -915, 'top': 895, 'width': 17, 'height': 24}
STREET_CARD5_SUIT_REGION = {'left': -829, 'top': 895, 'width': 17, 'height': 24}

# Пути к шаблонам мастей
SUIT_TEMPLATES = {
    '♠': 'templates/spades.png',
    '♥': 'templates/hearts.png',
    '♦': 'templates/diamonds.png',
    '♣': 'templates/clubs.png'
}

# Пути к шаблонам номеров
NUMBER_TEMPLATES = {
    '2': 'number_templates/2.png',
    '3': 'number_templates/3.png',
    '4': 'number_templates/4.png',
    '5': 'number_templates/5.png',
    '6': 'number_templates/6.png',
    '7': 'number_templates/7.png',
    '8': 'number_templates/8.png',
    '9': 'number_templates/9.png',
    '10': 'number_templates/10.png',
    'J': 'number_templates/J.png',
    'Q': 'number_templates/Q.png',
    'K': 'number_templates/K.png',
    'A': 'number_templates/A.png'
}

# =========================
# Функции для захвата и обработки экрана
# =========================

def capture_pixel_color(coord):
    """
    Захватывает цвет одного пикселя на экране.
    """
    with mss.mss() as sct:
        monitor = {
            "left": coord['left'],
            "top": coord['top'],
            "width": 1,
            "height": 1
        }
        try:
            sct_img = sct.grab(monitor)
            pixel = np.array(sct_img)[0, 0]
            return tuple(pixel[:3])  # Возвращаем только B, G, R
        except mss.exception.ScreenShotError as e:
            logging.error(f"Ошибка захвата пикселя ({coord['left']}, {coord['top']}): {e}")
            return None

def is_dealer_present(pixel_color, r_min=200, r_max=255):
    """
    Проверяет, находится ли дилер на основе значения красного канала (R) пикселя.
    """
    if pixel_color is None:
        return False
    b, g, r = pixel_color
    logging.debug(f"Проверка пикселя дилера - B: {b}, G: {g}, R: {r}")
    return r_min <= r <= r_max

def is_player_active(pixel_color, r_target, tolerance=5):
    """
    Проверяет, активен ли игрок на основе значения красного канала (R) пикселя.
    """
    if pixel_color is None:
        return False
    b, g, r = pixel_color
    logging.debug(f"Проверка пикселя активного игрока - B: {b}, G: {g}, R: {r} | Целевой R: {r_target}")
    return (r_target - tolerance) <= r <= (r_target + tolerance)

def find_dealer_seat():
    """
    Ищет позицию дилера среди заданных пикселей.
    """
    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = {executor.submit(capture_pixel_color, coord): idx for idx, coord in enumerate(PIXEL_DEALER_COORDS)}
        for future in concurrent.futures.as_completed(futures):
            idx = futures[future]
            try:
                pixel_color = future.result()
                if is_dealer_present(pixel_color):
                    logging.info(f"Dealer найден на Seat {idx + 1}")
                    return idx
            except Exception as e:
                logging.error(f"Ошибка при обработке Seat {idx + 1}: {e}")
    logging.warning("Dealer не найден")
    return None

def find_active_players(dealer_seat):
    """
    Ищет активных игроков в раздаче на основе заданных пикселей.
    """
    active_positions = []
    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = {executor.submit(capture_pixel_color, coord): idx for idx, coord in enumerate(PIXEL_INGAME_COORDS_R)}
        for future in concurrent.futures.as_completed(futures):
            idx = futures[future]
            seat_index = SEAT_INDICES_TO_CHECK[idx]
            try:
                pixel_color = future.result()
                target_r = PIXEL_INGAME_COORDS_R[idx]['r']
                if is_player_active(pixel_color, target_r, tolerance=5):
                    relative_pos = (seat_index - dealer_seat) % 8
                    position = POSITIONS[relative_pos]
                    position = position.lower()
                    if seat_index != YOUR_SEAT_INDEX:
                        active_positions.append(position)
            except Exception as e:
                logging.error(f"Ошибка при обработке Seat {seat_index + 1}: {e}")
    number_of_players = len(active_positions)
    return active_positions, number_of_players

def determine_player_position(dealer_seat):
    """
    Определяет позицию игрока на основе позиции дилера.
    """
    if dealer_seat is None:
        return {"position": "Unknown"}

    relative_pos = (YOUR_SEAT_INDEX - dealer_seat) % 8
    position = POSITIONS[relative_pos]

    return {"position": position}

def capture_pot_amount(region):
    """
    Захватывает изображение области pot и распознаёт сумму с использованием pytesseract.
    """
    with mss.mss() as sct:
        monitor = {
            "left": region['left'],
            "top": region['top'],
            "width": region['width'],
            "height": region['height']
        }
        try:
            sct_img = sct.grab(monitor)
            img = Image.frombytes('RGB', sct_img.size, sct_img.rgb)
            img = img.convert('L')  # Конвертируем в оттенки серого
            img = img.point(lambda x: 0 if x < 128 else 255, '1')  # Бинаризация
            pot_text = pytesseract.image_to_string(img, config='--psm 7 -c tessedit_char_whitelist=0123456789,.')
            match = re.search(r'(\d+[.,]?\d*)', pot_text)
            if match:
                number = match.group(1).replace(',', '.')
                logging.info(f"Распознанная сумма в банке: {number} BB")
                return float(number)
            else:
                logging.warning("Не удалось распознать сумму в банке.")
                return 0.0
        except Exception as e:
            logging.error(f"Ошибка при захвате или распознавании pot: {e}")
            return 0.0

def get_pot_amount():
    """
    Получает сумму в банке (pot) с помощью OCR.
    """
    pot_amount = capture_pot_amount(POT_REGION)
    return pot_amount

def capture_card_image(region):
    """
    Захватывает изображение заданной области экрана.
    """
    with mss.mss() as sct:
        monitor = {
            "left": region['left'],
            "top": region['top'],
            "width": region['width'],
            "height": region['height']
        }
        try:
            sct_img = sct.grab(monitor)
            img = Image.frombytes('RGB', sct_img.size, sct_img.rgb)
            return img
        except mss.exception.ScreenShotError as e:
            logging.error(f"Ошибка захвата области карт ({region['left']}, {region['top']}): {e}")
            return None

# =========================
# Функции для распознавания карт
# =========================

def recognize_card_number_template(img, card_number):
    """
    Распознаёт номер карты из изображения с использованием template matching.
    """
    try:
        img_cv = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2GRAY)

        best_match = None
        max_val = -np.inf

        for number, template_path in NUMBER_TEMPLATES.items():
            if not os.path.exists(template_path):
                logging.error(f"Шаблон для номера {number} не найден по пути: {template_path}")
                continue

            template = cv2.imread(template_path, cv2.IMREAD_GRAYSCALE)
            if template is None:
                logging.error(f"Не удалось загрузить шаблон для номера {number} из файла: {template_path}")
                continue

            # Проверка размеров изображений
            if img_cv.shape[0] < template.shape[0] or img_cv.shape[1] < template.shape[1]:
                scale_x = template.shape[1] / img_cv.shape[1]
                scale_y = template.shape[0] / img_cv.shape[0]
                scale = max(scale_x, scale_y)
                new_size = (int(img_cv.shape[1] * scale), int(img_cv.shape[0] * scale))
                img_cv_resized = cv2.resize(img_cv, new_size, interpolation=cv2.INTER_LINEAR)
                logging.debug(f"Масштабирование изображения номера карты {card_number} до размера шаблона номера {number}.")
            else:
                img_cv_resized = img_cv

            res = cv2.matchTemplate(img_cv_resized, template, cv2.TM_CCOEFF_NORMED)
            min_val, current_max_val, min_loc, max_loc = cv2.minMaxLoc(res)

            logging.debug(f"Сопоставление номера {number}: {current_max_val}")

            if current_max_val > max_val:
                max_val = current_max_val
                best_match = number

        MATCH_THRESHOLD = 0.4  # Настройте этот параметр в зависимости от качества шаблонов и изображений

        if best_match and max_val >= MATCH_THRESHOLD:
            logging.info(f"Распознанный номер карты {card_number}: '{best_match}'")
            return best_match
        else:
            logging.warning(f"Номер карты {card_number} не распознан или совпадение ниже порога.")
            return "?"
    except cv2.error as e:
        logging.error(f"Ошибка OpenCV при распознавании номера карты {card_number}: {e}")
        return "?"
    except Exception as e:
        logging.error(f"Ошибка при распознавании номера карты {card_number}: {e}")
        return "?"

def recognize_card_suit(img, card_number):
    """
    Распознаёт масть карты из изображения с использованием template matching.
    """
    try:
        img_cv = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2GRAY)

        best_match = None
        max_val = -np.inf

        for suit, template_path in SUIT_TEMPLATES.items():
            if not os.path.exists(template_path):
                logging.error(f"Шаблон для масти {suit} не найден по пути: {template_path}")
                continue

            template = cv2.imread(template_path, cv2.IMREAD_GRAYSCALE)
            if template is None:
                logging.error(f"Не удалось загрузить шаблон для масти {suit} из файла: {template_path}")
                continue

            res = cv2.matchTemplate(img_cv, template, cv2.TM_CCOEFF_NORMED)
            min_val, current_max_val, min_loc, max_loc = cv2.minMaxLoc(res)

            logging.debug(f"Сопоставление масти {suit}: {current_max_val}")

            if current_max_val > max_val:
                max_val = current_max_val
                best_match = suit

        MATCH_THRESHOLD = 0.0  # В вашем рабочем скрипте порог был 0.0, оставим так для совместимости

        if best_match and max_val >= MATCH_THRESHOLD:
            logging.info(f"Распознанная масть карты {card_number}: '{best_match}'")
            return best_match
        else:
            logging.warning(f"Масть карты {card_number} не распознана или совпадение ниже порога.")
            return "?"
    except Exception as e:
        logging.error(f"Ошибка при распознавании масти карты {card_number}: {e}")
        return "?"

def capture_card(card_number, number_region, suit_region):
    """
    Захватывает и распознаёт номер и масть карты.
    """
    # Захват номера карты
    number_img = capture_card_image(number_region)
    if number_img is None:
        return "Unknown"

    # Распознавание номера карты с использованием template matching
    card_text = recognize_card_number_template(number_img, card_number)
    if card_text == "?":
        logging.warning(f"Номер карты {card_number} не распознан.")
        return "Unknown"

    # Захват масти карты
    suit_img = capture_card_image(suit_region)
    if suit_img is None:
        suit_symbol = "?"
    else:
        suit_symbol = recognize_card_suit(suit_img, card_number)
        if suit_symbol == "?":
            logging.warning(f"Масть карты {card_number} не распознана.")

    if suit_symbol != "?":
        return f"{card_text}{suit_symbol}"
    else:
        return f"{card_text}?"

# =========================
# Функции для расчётов метрик
# =========================

def poker_metrics(data, equity=None, hand_strength=None):
    """
    Функция принимает словарь с данными, Equity и силу руки, возвращает метрики для принятия решений.
    Входные данные (словарь data):
    - pot: Размер текущего банка
    - bet_sizes: Словарь с размерами ставок для разных решений
    - stack: Размер эффективного стека игрока
    - position: Позиция игрока ('UTG', 'MP', 'CO', 'BTN', 'SB', 'BB')
    - stage: Стадия игры ('pre-flop', 'flop', 'turn', 'river')
    - table_cards: Карты на столе (список строк, например ['As', 'Kh', 'Qc'])
    - player_hand: Рука игрока (список строк, например ['Ad', 'Ks'])
    - players_before: Количество игроков до вас
    - players_after: Количество игроков после вас
    - outs: Количество аутов
    """
    # Распакуем данные
    pot = data["pot"]
    bet_sizes = data["bet_sizes"]  # Словарь с размерами ставок
    stack = data["stack"]
    stage = data["stage"]
    table_cards = data.get("table_cards", [])
    player_hand = data.get("player_hand", [])
    players_before = data.get("players_before", 0)
    players_after = data.get("players_after", 0)
    outs = data.get("outs", 0)
    hand_strength = data.get("hand_strength", None)
    
    # 1. Pot Odds
    pot_odds = {}
    for decision, bet in bet_sizes.items():
        pot_odds[decision] = bet / (pot + bet) if (pot + bet) > 0 else 0

    # 2. Win Probability (%) based on equity
    if stage.lower() in ['pre-flop', 'flop', 'turn', 'river']:
        if equity is not None:
            win_probability = equity * 100  # В процентах
        else:
            win_probability = "N/A"
    else:
        win_probability = "N/A"

    # 3. Hand Strength Description
    if hand_strength is not None:
        if hand_strength <= 100:
            hand_strength_desc = 'Сильная'
        elif 101 <= hand_strength <= 200:
            hand_strength_desc = 'Средняя'
        else:
            hand_strength_desc = 'Слабая'
    else:
        hand_strength_desc = 'Unknown'

    # 4. Expected Value (EV) для каждого решения
    ev = {}
    if stage.lower() in ['pre-flop', 'flop', 'turn', 'river']:
        for decision, bet in bet_sizes.items():
            if decision == "Фолд":
                # При фолде EV равен 0, так как вы не участвуете в раздаче
                ev[decision] = 0
            else:
                if equity is not None:
                    # Используем equity для расчёта EV
                    win_chance = equity
                    lose_chance = 1 - equity
                    ev_value = (win_chance * (pot + bet)) - (lose_chance * bet)
                    ev[decision] = ev_value
                else:
                    ev[decision] = "N/A"
    else:
        for decision, bet in bet_sizes.items():
            ev[decision] = "N/A"

    # 5. Stack-to-Pot Ratio (SPR)
    spr = round(stack / pot, 3) if pot > 0 else "Unknown"

    # 6. Outs
    if stage.lower() in ['pre-flop', 'flop', 'turn', 'river']:
        outs_display = outs if outs is not None else "N/A"
    else:
        outs_display = "N/A"

    # Вернем результаты
    return {
        "Pot Odds": {k: round(v, 3) for k, v in pot_odds.items()},
        "Expected Value (EV)": {k: (round(v, 3) if isinstance(v, float) else v) for k, v in ev.items()},
        "Stack-to-Pot Ratio (SPR)": spr,
        "Hand Strength (treys)": hand_strength,
        "Hand Strength Description": hand_strength_desc,
        "Outs": outs_display,
        "Win Probability (%)": round(win_probability, 2) if isinstance(win_probability, float) else win_probability
    }


def convert_cards_to_treys_format(cards_str):
    """
    Преобразует строку карт из формата 'As♠, Kh♥' в список ['As', 'Kh'] или ['As', 'Kh', 'Qc'].
    Не требует строго определенного количества карт.
    """
    suit_mapping = {
        '♠': 's',
        '♥': 'h',
        '♦': 'd',
        '♣': 'c'
    }
    if not cards_str or cards_str == "Не удалось определить некоторые карты.":
        return []
    cards = cards_str.split(', ')
    treys_cards = []
    seen_cards = set()
    for card in cards:
        if len(card) < 2:
            continue
        number = card[:-1]
        suit = suit_mapping.get(card[-1], '')
        treys_card = f"{number}{suit}"
        if len(treys_card) == 2 and number in '23456789TJQKA' and suit in 'shdc':
            if treys_card in seen_cards:
                logging.error(f"Дубликат карты обнаружен: {treys_card}")
                continue  # Пропустить дубликат
            treys_cards.append(treys_card)
            seen_cards.add(treys_card)
        else:
            treys_cards.append("??")  # Некорректная карта
    # Удаление некорректных карт
    if "??" in treys_cards:
        logging.error("Некорректные карты распознаны.")
        treys_cards = [card for card in treys_cards if card != "??"]
    return treys_cards

def calculate_outs(player_hand, board, stage):
    """
    Рассчитывает количество аутов на основе текущей руки и карт на столе.
    Возвращает количество аутов и текущую силу руки.
    """
    evaluator = Evaluator()
    deck = Deck()
    
    # Преобразуем карты в формат treys
    try:
        hand = [Card.new(c) for c in player_hand]
        board_cards = [Card.new(c) for c in board]
    except Exception as e:
        logging.error(f"Ошибка при преобразовании карт: {e}")
        return 0, None

    # Удаляем известные карты из колоды
    known_cards = hand + board_cards
    remaining_deck = [card for card in deck.cards if card not in known_cards]

    # Оцениваем текущую силу руки
    try:
        current_strength = evaluator.evaluate(hand, board_cards)
    except KeyError as e:
        logging.error(f"Ошибка при оценке силы руки: {e}")
        return 0, None

    outs = 0
    for card in remaining_deck:
        new_board = board_cards.copy()
        if stage.lower() in ["flop", "turn"]:
            if len(new_board) < 5:
                new_board.append(card)
        else:
            continue  # На river все карты уже на борде

        try:
            new_strength = evaluator.evaluate(hand, new_board)
            if new_strength < current_strength:
                outs += 1
        except KeyError as e:
            logging.error(f"Ошибка при оценке силы руки с добавленной картой: {e}")
            continue

    return outs, current_strength

# =========================
# Функции для Monte Carlo симуляций
# =========================

def generate_hand_from_range(range_list, used_cards):
    deck = Deck()
    for card in used_cards:
        if card in deck.cards:
            deck.cards.remove(card)
    if 'random' in range_list:
        # Возвращаем случайную руку из оставшейся колоды
        return [deck.draw(1)[0], deck.draw(1)[0]]
    else:
        # Преобразуем диапазон в список возможных комбинаций карт
        possible_hands = []
        for hand_str in range_list:
            # Определяем, suited или offsuit
            if 's' in hand_str:
                suited = True
                ranks = hand_str.replace('s', '')
            elif 'o' in hand_str:
                suited = False
                ranks = hand_str.replace('o', '')
            else:
                suited = False
                ranks = hand_str

            if len(ranks) != 2:
                continue  # Некорректный формат

            rank1, rank2 = ranks

            for suit1 in 'cdhs':
                for suit2 in 'cdhs':
                    if suited and suit1 != suit2:
                        continue
                    if not suited and suit1 == suit2:
                        continue
                    card1 = Card.new(rank1 + suit1)
                    card2 = Card.new(rank2 + suit2)
                    if card1 in deck.cards and card2 in deck.cards and card1 != card2:
                        possible_hands.append([card1, card2])
        if possible_hands:
            hand = random.choice(possible_hands)
            deck.cards.remove(hand[0])
            deck.cards.remove(hand[1])
            return hand
        else:
            # Если нет доступных рук в диапазоне, возвращаем случайную руку
            return [deck.draw(1)[0], deck.draw(1)[0]]

def simulate_hand(args):
    hand_cards, board_cards, deck_cards, num_players, positions, stage = args
    evaluator = Evaluator()
    simulation_deck = Deck()
    simulation_deck.cards = deck_cards.copy()
    random.shuffle(simulation_deck.cards)

    used_cards = hand_cards + board_cards

    # Раздаем карты оппонентам
    opponents_hands = []
    for position in positions:
        range_list = position_ranges.get(position.capitalize(), ['random'])
        opp_hand = generate_hand_from_range(range_list, used_cards)
        used_cards.extend(opp_hand)
        opponents_hands.append(opp_hand)

    # Дополняем борд до 5 карт в зависимости от стадии
    remaining_board = []
    if stage.lower() == 'pre-flop':
        num_remaining_cards = 5
    elif stage.lower() == 'flop':
        num_remaining_cards = 5 - len(board_cards)
    elif stage.lower() == 'turn':
        num_remaining_cards = 5 - len(board_cards)
    elif stage.lower() == 'river':
        num_remaining_cards = 5 - len(board_cards)
    else:
        raise ValueError("Некорректная стадия игры. Допустимые значения: 'pre-flop', 'flop', 'turn', 'river'.")

    for _ in range(num_remaining_cards):
        if not simulation_deck.cards:
            break  # Нет больше карт в колоде
        card = simulation_deck.draw(1)[0]
        while card in used_cards:
            if not simulation_deck.cards:
                break
            card = simulation_deck.draw(1)[0]
        remaining_board.append(card)
        used_cards.append(card)

    full_board = board_cards + remaining_board

    # Оцениваем вашу руку
    try:
        my_score = evaluator.evaluate(hand_cards, full_board)
    except Exception as e:
        logging.error(f"Ошибка при оценке вашей руки: {e}")
        return 0  # Предполагаем поражение при ошибке

    # Оцениваем руки оппонентов
    opp_scores = []
    for opp_hand in opponents_hands:
        try:
            opp_score = evaluator.evaluate(opp_hand, full_board)
            opp_scores.append(opp_score)
        except Exception as e:
            logging.error(f"Ошибка при оценке руки оппонента: {e}")
            opp_scores.append(float('inf'))  # Предполагаем, что оппонент проигрывает

    if not opp_scores:
        # Если нет оппонентов, автоматически выигрываем
        return 1  # Победа

    best_opp_score = min(opp_scores)

    if my_score < best_opp_score:
        return 1  # Победа
    elif my_score == best_opp_score:
        return 0.5  # Ничья
    else:
        return 0  # Поражение

def calculate_win_probability_threaded(hand, board, num_players, num_simulations=1000, hero_position='UTG', stage='pre-flop'):
    # Инициализация
    hand_cards = [Card.new(card) for card in hand]
    board_cards = [Card.new(card) for card in board]

    # Удаляем известные карты из колоды
    deck = Deck()
    known_cards = hand_cards + board_cards
    for card in known_cards:
        if card in deck.cards:
            deck.cards.remove(card)
    deck_cards = deck.cards.copy()

    # Определяем позиции оппонентов
    positions = ['UTG', 'MP', 'CO', 'BTN', 'SB', 'BB']
    # Удаляем позицию героя
    if hero_position.capitalize() in positions:
        positions.remove(hero_position.capitalize())
    # Если игроков меньше, сокращаем список позиций
    positions = positions[:num_players]  # Исправлено: убрано -1

    # Подготовка аргументов для параллельной обработки
    args = [(hand_cards, board_cards, deck_cards, num_players, positions, stage) for _ in range(num_simulations)]

    wins = 0
    with concurrent.futures.ThreadPoolExecutor() as executor:
        results = executor.map(simulate_hand, args)
        for result in results:
            wins += result

    win_probability = wins / num_simulations
    return win_probability

# =========================
# Функции для расчёта EV
# =========================

def calculate_expected_value(win_prob, pot, bet_size):
    expected_win = win_prob * (pot + bet_size)
    expected_loss = (1 - win_prob) * bet_size
    expected_value = expected_win - expected_loss
    return expected_value

# =========================
# Основная функция и GUI
# =========================

def main():
    global RESULT
    # Настройка логирования
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

    # Создание GUI
    root = tk.Tk()
    root.title("Анализ стола покера")

    # Верхняя часть - Вывод RESULT
    top_frame = tk.Frame(root, padx=10, pady=10)
    top_frame.pack(fill=tk.BOTH, expand=True)

    top_label = tk.Label(top_frame, text="Собранная информация:", font=("Arial", 14, "bold"))
    top_label.pack(anchor='w')

    result_text = tk.Text(top_frame, height=10, width=100)
    result_text.pack()
    result_text.config(state=tk.DISABLED)

    # Средняя часть - Кнопка "Сбор данных"
    middle_frame = tk.Frame(root, padx=10, pady=10)
    middle_frame.pack(fill=tk.BOTH, expand=True)

    collect_button = tk.Button(middle_frame, text="Сбор данных", font=("Arial", 12, "bold"), width=20, height=2)
    collect_button.pack(pady=10)

    # Нижняя часть - Вывод метрик и рекомендации
    bottom_frame = tk.Frame(root, padx=10, pady=10)
    bottom_frame.pack(fill=tk.BOTH, expand=True)

    metrics_label = tk.Label(bottom_frame, text="Результаты метрик:", font=("Arial", 14, "bold"))
    metrics_label.pack(anchor='w')

    metrics_text = tk.Text(bottom_frame, height=15, width=100)
    metrics_text.pack()
    metrics_text.config(state=tk.DISABLED)

    # Рекомендации для разных решений
    recommendation_frame = tk.Frame(bottom_frame, padx=10, pady=10)
    recommendation_frame.pack(fill=tk.BOTH, expand=True)

    recommendations = ["Фолд", "Колл 1 ББ", "Рейз 3 ББ"]
    recommendation_textboxes = {}

    for rec in recommendations:
        rec_label = tk.Label(recommendation_frame, text=f"Рекомендация: {rec}", font=("Arial", 14, "bold"))
        rec_label.pack(anchor='w', pady=(10,0))

        rec_text = tk.Text(recommendation_frame, height=2, width=100)
        rec_text.pack()
        rec_text.config(state=tk.DISABLED)

        recommendation_textboxes[rec] = rec_text

    def on_collect_data():
        global RESULT
        # Очистка предыдущих результатов
        RESULT = {}
        result_text.config(state=tk.NORMAL)
        result_text.delete(1.0, tk.END)
        result_text.config(state=tk.DISABLED)
        metrics_text.config(state=tk.NORMAL)
        metrics_text.delete(1.0, tk.END)
        metrics_text.config(state=tk.DISABLED)
        for rec in recommendations:
            recommendation_textboxes[rec].config(state=tk.NORMAL)
            recommendation_textboxes[rec].delete(1.0, tk.END)
            recommendation_textboxes[rec].config(state=tk.DISABLED)

        # Настройка логирования
        logging.info("Начало анализа стола...")

        # -------------------------
        # Определение позиции дилера и активных игроков
        # -------------------------
        dealer_seat = find_dealer_seat()

        if dealer_seat is None:
            messagebox.showerror("Ошибка", "Не удалось определить позицию дилера.")
            return

        player_position = determine_player_position(dealer_seat)
        active_positions, number_of_players = find_active_players(dealer_seat)
        pot_amount = get_pot_amount()
        pot_amount_display = pot_amount if pot_amount else 0.0

        logging.info(f"Позиция игрока: {player_position['position']}")
        logging.info(f"Количество активных игроков: {number_of_players}")
        logging.info(f"Позиции активных игроков: {', '.join(active_positions)}")
        logging.info(f"Сумма в банке (pot): {pot_amount_display} BB")

        # -------------------------
        # Распознавание ваших карт
        # -------------------------
        my_card = capture_card("MyCard1", HAND_CARD1_NUMBER_REGION, HAND_CARD1_SUIT_REGION)
        my_card2 = capture_card("MyCard2", HAND_CARD2_NUMBER_REGION, HAND_CARD2_SUIT_REGION)
        my_cards = []
        if my_card != "Unknown":
            my_cards.append(my_card)
        else:
            my_cards.append("Не удалось определить")
        if my_card2 != "Unknown":
            my_cards.append(my_card2)
        else:
            my_cards.append("Не удалось определить")
        my_card_display = ", ".join(my_cards) if all(card != "Не удалось определить" for card in my_cards) else "Не удалось определить некоторые карты."

        logging.info(f"Ваши карты: {my_card_display}")

        # -------------------------
        # Распознавание карт на столе
        # -------------------------
        street_cards = []
        street_cards_regions = [
            ("1", STREET_CARD1_NUMBER_REGION, STREET_CARD1_SUIT_REGION),
            ("2", STREET_CARD2_NUMBER_REGION, STREET_CARD2_SUIT_REGION),
            ("3", STREET_CARD3_NUMBER_REGION, STREET_CARD3_SUIT_REGION),
            ("4", STREET_CARD4_NUMBER_REGION, STREET_CARD4_SUIT_REGION),
            ("5", STREET_CARD5_NUMBER_REGION, STREET_CARD5_SUIT_REGION)
        ]

        for card_num, number_region, suit_region in street_cards_regions:
            card = capture_card(card_num, number_region, suit_region)
            if card == "Unknown":
                street_cards.append("Не удалось определить")
            else:
                street_cards.append(card)

        recognized_street_cards = [card for card in street_cards if card != "Не удалось определить"]
        num_street_cards = len(recognized_street_cards)

        if num_street_cards >= 5:
            stage = "river"
        elif num_street_cards == 4:
            stage = "turn"
        elif num_street_cards == 3:
            stage = "flop"
        else:
            stage = "pre-flop"

        street_display = ", ".join(recognized_street_cards) if recognized_street_cards else "Карты на столе не распознаны."
        stage_display = stage.capitalize()

        logging.info(f"Карты на столе: {street_display}")
        logging.info(f"Текущая стадия: {stage_display}")

        # -------------------------
        # Формирование итогового вывода
        # -------------------------
        result = {
            "Position": player_position['position'],
            "Number of Players": number_of_players,
            "Active Positions": ', '.join(active_positions),
            "Pot (BB)": pot_amount_display,
            "My Cards": my_card_display,
            "Street Cards": street_display,
            "Stage": stage_display
        }

        RESULT = result

        # -------------------------
        # Обновление GUI с результатами
        # -------------------------
        result_text.config(state=tk.NORMAL)
        result_str = "\n".join([f"{key}: {value}" for key, value in RESULT.items()])
        result_text.insert(tk.END, result_str)
        result_text.config(state=tk.DISABLED)

        # -------------------------
        # Автоматический расчёт аутов и силы руки
        # -------------------------
        player_hand_treys = convert_cards_to_treys_format(RESULT.get("My Cards", ""))
        table_cards_treys = convert_cards_to_treys_format(RESULT.get("Street Cards", ""))
        stage = stage_display.lower()

        logging.debug(f"player_hand_treys: {player_hand_treys}")
        logging.debug(f"table_cards_treys: {table_cards_treys}")

        # Проверка валидности карт
        valid_ranks = set('23456789TJQKA')
        valid_suits = set('shdc')

        def is_valid_card(card):
            return len(card) == 2 and card[0] in valid_ranks and card[1] in valid_suits

        # Проверяем руку игрока
        if not all(is_valid_card(card) for card in player_hand_treys):
            messagebox.showerror("Ошибка", "Некорректные данные карт вашей руки для симуляции.")
            logging.error("Некорректные данные карт вашей руки для симуляции.")
            return

        # Проверяем карты на столе, в зависимости от стадии
        expected_table_cards = {
            'pre-flop': 0,
            'flop': 3,
            'turn': 4,
            'river': 5
        }.get(stage, 0)

        if expected_table_cards > 0:
            if len(table_cards_treys) != expected_table_cards:
                messagebox.showerror("Ошибка", f"Некорректное количество карт на столе для стадии {stage_display}. Ожидалось {expected_table_cards}, распознано {len(table_cards_treys)}.")
                logging.error(f"Некорректное количество карт на столе для стадии {stage_display}. Ожидалось {expected_table_cards}, распознано {len(table_cards_treys)}.")
                return
            if not all(is_valid_card(card) for card in table_cards_treys):
                messagebox.showerror("Ошибка", "Некорректные данные карт на столе для симуляции.")
                logging.error("Некорректные данные карт на столе для симуляции.")
                return
        else:
            if len(table_cards_treys) != 0:
                messagebox.showerror("Ошибка", f"На стадии {stage_display} не должно быть карт на столе.")
                logging.error(f"На стадии {stage_display} не должно быть карт на столе.")
                return

        # Теперь, если карты валидны, выполняем симуляцию и расчет outs
        if stage in ['pre-flop', 'flop', 'turn', 'river']:
            if stage == 'pre-flop':
                outs = "N/A"
                hand_strength = None
                logging.info("Симуляция аутов не выполняется на стадии префлоп.")
            else:
                outs, hand_strength = calculate_outs(player_hand_treys, table_cards_treys, stage)
                if hand_strength is None:
                    logging.info("Сила руки не может быть оценена.")
                else:
                    logging.info(f"Количество аутов: {outs if outs is not None else 'N/A'}")
                    logging.info(f"Сила руки (treys): {hand_strength if hand_strength is not None else 'N/A'}")
        else:
            outs, hand_strength = "N/A", None

        # -------------------------
        # Подготовка данных для метрик
        # -------------------------
        game_data = {
            "pot": pot_amount_display,
            "bet_sizes": {
                "Фолд": 0,
                "Колл 1 ББ": 1,    # Предполагаем, что 1 ББ
                "Рейз 3 ББ": 3     # Предполагаем, что 3 ББ
            },
            "stack": 200,  # Здесь вы можете добавить логику для определения стека
            "position": RESULT.get("Position", "Unknown"),
            "stage": stage,
            "table_cards": table_cards_treys,
            "player_hand": player_hand_treys,
            "players_before": 0,  # Можно добавить логику для определения
            "players_after": number_of_players,
            "outs": outs if stage in ['pre-flop', 'flop', 'turn', 'river'] else "N/A",
            "hand_strength": hand_strength
        }

        # -------------------------
        # Расчет Equity с помощью Monte Carlo симуляций
        # -------------------------
        if stage in ['pre-flop', 'flop', 'turn', 'river']:
            # Преобразуем карты в формат treys
            hand = player_hand_treys  # Список ['As', 'Kh']
            board = table_cards_treys  # Список ['Ks', '5s', 'As']

            win_prob = calculate_win_probability_threaded(
                hand=hand,
                board=board,
                num_players=number_of_players,
                num_simulations=1000,
                hero_position=RESULT.get("Position", "Dealer"),
                stage=stage
            )

            logging.info(f"Расчитанная вероятность выигрыша: {win_prob * 100:.2f}%")
        else:
            win_prob = None

        # -------------------------
        # Расчет метрик
        # -------------------------
        metrics = poker_metrics(game_data, equity=win_prob, hand_strength=hand_strength)

        # -------------------------
        # Определение рекомендации для каждого решения
        # -------------------------
        recommendations_results = {}
        for decision, ev_value in metrics["Expected Value (EV)"].items():
            recommendations_results[decision] = f"EV для {decision}: {ev_value}"

        # -------------------------
        # Отображение метрик
        # -------------------------
        metrics_text.config(state=tk.NORMAL)
        pot_odds_str = "\n".join([f"{k}: {v}" for k, v in metrics["Pot Odds"].items()])
        metrics_str = f"Pot Odds:\n{pot_odds_str}\n\n"
        metrics_str += f"Expected Value (EV):\n"
        for k, v in metrics["Expected Value (EV)"].items():
            metrics_str += f"  {k}: {v}\n"
        metrics_str += f"\nStack-to-Pot Ratio (SPR): {metrics['Stack-to-Pot Ratio (SPR)']}\n"
        metrics_str += f"Hand Strength (treys): {metrics['Hand Strength (treys)']}\n"
        metrics_str += f"Hand Strength Description: {metrics['Hand Strength Description']}\n"
        metrics_str += f"Outs: {metrics['Outs']}\n"
        metrics_str += f"Win Probability (%): {metrics['Win Probability (%)']}\n"
        metrics_text.insert(tk.END, metrics_str)
        metrics_text.config(state=tk.DISABLED)

        # -------------------------
        # Отображение рекомендаций
        # -------------------------
        for decision, rec_text in recommendations_results.items():
            if decision in recommendation_textboxes:
                recommendation_textboxes[decision].config(state=tk.NORMAL)
                recommendation_textboxes[decision].insert(tk.END, rec_text)
                recommendation_textboxes[decision].config(state=tk.DISABLED)

    collect_button.config(command=on_collect_data)

    # Запуск главного цикла
    root.mainloop()

if __name__ == "__main__":
    main()
