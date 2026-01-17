"""
Card recognition using template matching and OCR.
Handles card detection, validation, and deduplication.
"""
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import logging
import os

import cv2
import numpy as np
from PIL import Image

from ..app.config import Region, VisionConfig, TEMPLATES_DIR, NUMBER_TEMPLATES_DIR
from ..poker.models import Card, HoleCards, BoardCards


logger = logging.getLogger(__name__)


@dataclass
class RecognitionResult:
    """Result of a card recognition attempt."""
    card: Optional[Card]
    confidence: float
    raw_rank: str
    raw_suit: str
    is_valid: bool
    error: Optional[str] = None


class TemplateCache:
    """Caches loaded template images."""
    
    def __init__(self):
        self._rank_templates: Dict[str, np.ndarray] = {}
        self._suit_templates: Dict[str, np.ndarray] = {}
        self._loaded = False
    
    def load_templates(
        self,
        rank_dir: Path = NUMBER_TEMPLATES_DIR,
        suit_dir: Path = TEMPLATES_DIR
    ) -> bool:
        """
        Load all template images from directories.
        
        Returns:
            True if templates loaded successfully
        """
        if self._loaded:
            return True
        
        # Rank templates (2-A)
        rank_files = {
            "2": "2.png", "3": "3.png", "4": "4.png", "5": "5.png",
            "6": "6.png", "7": "7.png", "8": "8.png", "9": "9.png",
            "T": "10.png", "J": "J.png", "Q": "Q.png", "K": "K.png", "A": "A.png"
        }
        
        for rank, filename in rank_files.items():
            path = rank_dir / filename
            if path.exists():
                template = cv2.imread(str(path), cv2.IMREAD_GRAYSCALE)
                if template is not None:
                    self._rank_templates[rank] = template
                else:
                    logger.warning(f"Failed to load rank template: {path}")
            else:
                logger.debug(f"Rank template not found: {path}")
        
        # Suit templates
        suit_files = {
            "s": "spades.png",
            "h": "hearts.png",
            "d": "diamonds.png",
            "c": "clubs.png"
        }
        
        for suit, filename in suit_files.items():
            path = suit_dir / filename
            if path.exists():
                template = cv2.imread(str(path), cv2.IMREAD_GRAYSCALE)
                if template is not None:
                    self._suit_templates[suit] = template
                else:
                    logger.warning(f"Failed to load suit template: {path}")
            else:
                logger.debug(f"Suit template not found: {path}")
        
        self._loaded = len(self._rank_templates) > 0 or len(self._suit_templates) > 0
        logger.info(
            f"Loaded {len(self._rank_templates)} rank templates, "
            f"{len(self._suit_templates)} suit templates"
        )
        return self._loaded
    
    @property
    def rank_templates(self) -> Dict[str, np.ndarray]:
        return self._rank_templates
    
    @property
    def suit_templates(self) -> Dict[str, np.ndarray]:
        return self._suit_templates


class CardRecognizer:
    """
    Recognizes cards from screen captures using template matching.
    """
    
    # Unicode suit mappings for UI format conversion
    SUIT_MAP = {
        "♠": "s", "♥": "h", "♦": "d", "♣": "c",
        "spade": "s", "heart": "h", "diamond": "d", "club": "c",
    }
    
    def __init__(self, config: Optional[VisionConfig] = None):
        """
        Initialize card recognizer.
        
        Args:
            config: Vision configuration (uses defaults if not provided)
        """
        self.config = config or VisionConfig()
        self._cache = TemplateCache()
    
    def load_templates(self) -> bool:
        """Load template images. Call before recognition."""
        return self._cache.load_templates()
    
    def _match_template(
        self,
        image: np.ndarray,
        templates: Dict[str, np.ndarray],
        threshold: float
    ) -> Tuple[Optional[str], float]:
        """
        Match image against templates.
        
        Returns:
            (matched_key, confidence) or (None, 0.0)
        """
        best_match = None
        best_confidence = -np.inf
        
        for key, template in templates.items():
            # Resize image if smaller than template
            if image.shape[0] < template.shape[0] or image.shape[1] < template.shape[1]:
                scale = max(
                    template.shape[1] / image.shape[1],
                    template.shape[0] / image.shape[0]
                )
                new_size = (
                    int(image.shape[1] * scale) + 1,
                    int(image.shape[0] * scale) + 1
                )
                image_scaled = cv2.resize(image, new_size, interpolation=cv2.INTER_LINEAR)
            else:
                image_scaled = image
            
            try:
                result = cv2.matchTemplate(image_scaled, template, cv2.TM_CCOEFF_NORMED)
                _, max_val, _, _ = cv2.minMaxLoc(result)
                
                if max_val > best_confidence:
                    best_confidence = max_val
                    best_match = key
            except cv2.error as e:
                logger.debug(f"Template match error for {key}: {e}")
                continue
        
        if best_match and best_confidence >= threshold:
            return best_match, best_confidence
        
        return None, best_confidence
    
    def recognize_rank(self, image: Image.Image) -> Tuple[Optional[str], float]:
        """
        Recognize card rank from image.
        
        Args:
            image: PIL Image of the rank portion
        
        Returns:
            (rank, confidence) or (None, 0.0)
        """
        if not self._cache.rank_templates:
            logger.warning("No rank templates loaded")
            return None, 0.0
        
        # Convert to grayscale numpy array
        img_gray = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2GRAY)
        
        return self._match_template(
            img_gray,
            self._cache.rank_templates,
            self.config.template_match_threshold
        )
    
    def recognize_suit(self, image: Image.Image) -> Tuple[Optional[str], float]:
        """
        Recognize card suit from image.
        
        Args:
            image: PIL Image of the suit portion
        
        Returns:
            (suit, confidence) or (None, 0.0)
        """
        if not self._cache.suit_templates:
            logger.warning("No suit templates loaded")
            return None, 0.0
        
        img_gray = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2GRAY)
        
        return self._match_template(
            img_gray,
            self._cache.suit_templates,
            self.config.suit_match_threshold
        )
    
    @staticmethod
    def recognize_suit_by_color(rgb: Tuple[int, int, int]) -> Tuple[str, float]:
        """
        Recognize card suit by pixel color.
        Much faster and more reliable than template matching.
        
        Colors:
        - Hearts (red): R > 150
        - Clubs (green): G > 100 and G > R and G > B
        - Diamonds (blue): B > 80 and B > R
        - Spades (black): everything else
        
        Args:
            rgb: (R, G, B) tuple
        
        Returns:
            (suit, confidence) - suit is 'h', 'c', 'd', or 's'
        """
        r, g, b = rgb
        
        # Hearts - red
        if r > 150 and r > g and r > b:
            return 'h', 1.0
        
        # Clubs - green
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
        suit_image: Image.Image
    ) -> RecognitionResult:
        """
        Recognize a complete card from rank and suit images.
        
        Args:
            rank_image: PIL Image of the rank
            suit_image: PIL Image of the suit
        
        Returns:
            RecognitionResult with card or error
        """
        rank, rank_conf = self.recognize_rank(rank_image)
        suit, suit_conf = self.recognize_suit(suit_image)
        
        confidence = min(rank_conf, suit_conf)
        
        if rank is None:
            return RecognitionResult(
                card=None,
                confidence=confidence,
                raw_rank="?",
                raw_suit=suit or "?",
                is_valid=False,
                error="Failed to recognize rank"
            )
        
        if suit is None:
            return RecognitionResult(
                card=None,
                confidence=confidence,
                raw_rank=rank,
                raw_suit="?",
                is_valid=False,
                error="Failed to recognize suit"
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
        - "K♥" -> Kh
        - "Ah" -> Ah
        - "10♠" -> Ts
        
        Args:
            ui_string: Card string from UI
        
        Returns:
            Card or None if invalid
        """
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
        suit = CardRecognizer.SUIT_MAP.get(suit_part, suit_part)
        
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
