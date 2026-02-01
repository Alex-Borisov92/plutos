"""
Card recognition using Tesseract OCR and color-based suit detection.

Handles card detection, validation, and deduplication.
- Rank recognition: Tesseract OCR
- Suit recognition: Color-based pixel detection (fast and reliable)
"""
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import logging
import re

import numpy as np
from PIL import Image

try:
    import pytesseract
    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False

from ..app.config import Region, VisionConfig, TESSERACT_PATH
from ..poker.models import Card, HoleCards, BoardCards


logger = logging.getLogger(__name__)

# Configure Tesseract path
if TESSERACT_AVAILABLE:
    pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH


@dataclass
class RecognitionResult:
    """Result of a card recognition attempt."""
    card: Optional[Card]
    confidence: float
    raw_rank: str
    raw_suit: str
    is_valid: bool
    error: Optional[str] = None


class CardRecognizer:
    """
    Recognizes cards from screen captures using OCR and color detection.
    
    - Ranks: Tesseract OCR with whitelist
    - Suits: Color-based pixel detection
    """
    
    # Map OCR output to standard rank notation
    RANK_MAP = {
        "1": "A",  # Sometimes OCR reads A as 1
        "0": "T",  # 10 -> T
        "10": "T",
        "l": "J",  # lowercase L -> J
        "i": "J",  # i -> J
        "O": "Q",  # O -> Q sometimes
    }
    
    # Valid ranks after normalization
    VALID_RANKS = frozenset("23456789TJQKA")
    
    def __init__(self, config: Optional[VisionConfig] = None):
        """
        Initialize card recognizer.
        
        Args:
            config: Vision configuration (uses defaults if not provided)
        """
        self.config = config or VisionConfig()
        
        if not TESSERACT_AVAILABLE:
            logger.warning("pytesseract not available, OCR disabled")
    
    def recognize_rank_ocr(self, image: Image.Image) -> Tuple[Optional[str], float]:
        """
        Recognize card rank using Tesseract OCR.
        
        Args:
            image: PIL Image of the rank portion
        
        Returns:
            (rank, confidence) or (None, 0.0)
        """
        if not TESSERACT_AVAILABLE:
            return None, 0.0
        
        try:
            # Preprocess image for better OCR
            img = image.convert('L')  # Grayscale
            img_array = np.array(img)
            
            # Increase contrast
            img_array = np.clip(img_array * 1.5, 0, 255).astype(np.uint8)
            
            # Threshold to binary
            threshold = 128
            img_array = np.where(img_array > threshold, 255, 0).astype(np.uint8)
            
            img_processed = Image.fromarray(img_array)
            
            # OCR with single character mode
            ocr_config = self.config.rank_ocr_config
            text = pytesseract.image_to_string(img_processed, config=ocr_config)
            text = text.strip().upper()
            
            if not text:
                return None, 0.0
            
            # Take first character/token
            rank = text[0] if len(text) == 1 else text[:2] if text.startswith("10") else text[0]
            
            # Normalize
            rank = self.RANK_MAP.get(rank, rank)
            
            if rank in self.VALID_RANKS:
                return rank, 0.9
            
            logger.debug(f"OCR result '{text}' not valid rank")
            return None, 0.0
            
        except Exception as e:
            logger.debug(f"OCR error: {e}")
            return None, 0.0
    
    @staticmethod
    def recognize_suit_by_color(rgb: Tuple[int, int, int]) -> Tuple[str, float]:
        """
        Recognize card suit by pixel color.
        Much faster and more reliable than template matching.
        
        Colors (Pokerdom):
        - Hearts (red): R > 150 and R > G and R > B
        - Clubs (green): G > 100 and G > R and G > B
        - Diamonds (blue): B > 80 and B > R
        - Spades (black/dark): everything else
        
        Args:
            rgb: (R, G, B) tuple
        
        Returns:
            (suit, confidence) - suit is 'h', 'c', 'd', or 's'
        """
        r, g, b = rgb
        
        # Hearts - red
        if r > 150 and r > g and r > b:
            return 'h', 1.0
        
        # Clubs - green (Pokerdom uses green for clubs)
        if g > 100 and g > r and g > b:
            return 'c', 1.0
        
        # Diamonds - blue
        if b > 80 and b > r:
            return 'd', 1.0
        
        # Spades - dark/black (all channels similar and low)
        return 's', 1.0
    
    def recognize_card(
        self,
        rank_image: Image.Image,
        suit_rgb: Tuple[int, int, int]
    ) -> RecognitionResult:
        """
        Recognize a complete card from rank image and suit color.
        
        Args:
            rank_image: PIL Image of the rank
            suit_rgb: RGB tuple from suit pixel
        
        Returns:
            RecognitionResult with card or error
        """
        rank, rank_conf = self.recognize_rank_ocr(rank_image)
        suit, suit_conf = self.recognize_suit_by_color(suit_rgb)
        
        confidence = min(rank_conf, suit_conf)
        
        if rank is None:
            return RecognitionResult(
                card=None,
                confidence=confidence,
                raw_rank="?",
                raw_suit=suit,
                is_valid=False,
                error="Failed to recognize rank"
            )
        
        # Validate card
        try:
            card = Card(rank=rank, suit=suit)
            return RecognitionResult(
                card=card,
                confidence=confidence,
                raw_rank=rank,
                raw_suit=suit,
                is_valid=True
            )
        except ValueError as e:
            return RecognitionResult(
                card=None,
                confidence=confidence,
                raw_rank=rank,
                raw_suit=suit,
                is_valid=False,
                error=str(e)
            )
    
    @staticmethod
    def convert_ui_card(ui_string: str) -> Optional[Card]:
        """
        Convert UI format card string to Card object.
        
        Handles formats like:
        - "K heart" -> Kh
        - "Ah" -> Ah
        - "10 spade" -> Ts
        
        Args:
            ui_string: Card string from UI
        
        Returns:
            Card or None if invalid
        """
        SUIT_MAP = {
            "spade": "s", "heart": "h", "diamond": "d", "club": "c",
            "spades": "s", "hearts": "h", "diamonds": "d", "clubs": "c",
        }
        
        ui_string = ui_string.strip()
        if not ui_string or len(ui_string) < 2:
            return None
        
        # Handle 10 -> T
        if ui_string.startswith("10"):
            rank = "T"
            suit_part = ui_string[2:]
        else:
            rank = ui_string[0].upper()
            suit_part = ui_string[1:]
        
        # Map suit
        suit_part = suit_part.strip().lower()
        suit = SUIT_MAP.get(suit_part, suit_part)
        
        # Validate
        if rank not in Card.VALID_RANKS:
            return None
        if suit not in Card.VALID_SUITS:
            return None
        
        try:
            return Card(rank=rank, suit=suit)
        except ValueError:
            return None
    
    @staticmethod
    def validate_card_string(card_str: str) -> bool:
        """
        Validate a card string in treys format (e.g., "Ah", "Ts").
        
        Args:
            card_str: Card string to validate
        
        Returns:
            True if valid
        """
        if len(card_str) != 2:
            return False
        return card_str[0] in Card.VALID_RANKS and card_str[1] in Card.VALID_SUITS


def recognize_stack_ocr(
    image: Image.Image,
    config: Optional[VisionConfig] = None
) -> Optional[float]:
    """
    Recognize player stack from image using OCR.
    
    Expects format like "151,52" or "25.5" (in BB).
    
    Args:
        image: PIL Image of stack region
        config: Vision config
    
    Returns:
        Stack in BB as float, or None if recognition failed
    """
    if not TESSERACT_AVAILABLE:
        return None
    
    config = config or VisionConfig()
    
    try:
        # Preprocess
        img = image.convert('L')
        img_array = np.array(img)
        
        # Threshold
        img_array = np.where(img_array > 100, 255, 0).astype(np.uint8)
        img_processed = Image.fromarray(img_array)
        
        # OCR
        text = pytesseract.image_to_string(
            img_processed,
            config=config.stack_ocr_config
        )
        text = text.strip()
        
        if not text:
            return None
        
        # Parse number (handle comma as decimal separator)
        text = text.replace(',', '.').replace(' ', '')
        
        # Remove non-numeric suffix (like "BB")
        text = re.sub(r'[^0-9.]', '', text)
        
        if text:
            return float(text)
        
        return None
        
    except Exception as e:
        logger.debug(f"Stack OCR error: {e}")
        return None


def convert_cards_list(
    card_strings: List[str],
    deduplicate: bool = True
) -> Tuple[List[Card], List[str]]:
    """
    Convert list of UI card strings to Card objects.
    
    Args:
        card_strings: List of card strings from UI
        deduplicate: Whether to remove duplicates
    
    Returns:
        (list of valid Cards, list of error messages)
    """
    cards = []
    errors = []
    seen = set()
    
    for s in card_strings:
        card = CardRecognizer.convert_ui_card(s)
        if card is None:
            errors.append(f"Invalid card: {s}")
            continue
        
        card_key = str(card)
        if deduplicate and card_key in seen:
            errors.append(f"Duplicate card: {card_key}")
            continue
        
        seen.add(card_key)
        cards.append(card)
    
    return cards, errors


def build_hole_cards(cards: List[Card]) -> Optional[HoleCards]:
    """
    Build HoleCards from list of cards.
    
    Args:
        cards: List of exactly 2 valid cards
    
    Returns:
        HoleCards or None if invalid
    """
    if len(cards) != 2:
        logger.debug(f"Expected 2 cards for hole cards, got {len(cards)}")
        return None
    
    return HoleCards(card1=cards[0], card2=cards[1])


def build_board_cards(cards: List[Card]) -> BoardCards:
    """
    Build BoardCards from list of cards.
    
    Args:
        cards: List of 0-5 valid cards
    
    Returns:
        BoardCards (empty if invalid count)
    """
    if len(cards) > 5:
        logger.warning(f"Too many board cards: {len(cards)}, using first 5")
        cards = cards[:5]
    
    return BoardCards(cards=tuple(cards))
