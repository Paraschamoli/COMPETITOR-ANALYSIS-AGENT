#!/usr/bin/env python3
"""
Business type classification and adaptation for the Competitor Analysis Agent
Provides rule-based business type detection and category-specific templates
"""

import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)

# Business type categories
FOOD = "food"
RETAIL = "retail"
SERVICE = "service"
TECH = "tech"
INDUSTRIAL = "industrial"
HEALTHCARE = "healthcare"
ENTERTAINMENT = "entertainment"
GENERAL = "general"

# Keyword mapping for classification
CATEGORY_KEYWORDS = {
    FOOD: [
        "cafe", "coffee shop", "restaurant", "bakery", "bar", "pub", "pizzeria",
        "sushi", "food truck", "bistro", "diner", "grill", "steakhouse",
        "brasserie", "canteen", "deli", "eatery", "fast food", "ice cream",
        "juice bar", "patisserie", "roastery", "tavern", "tea house"
    ],
    RETAIL: [
        "shop", "store", "boutique", "grocery", "market", "pharmacy", "bookstore",
        "clothing", "fashion", "shoe", "jewelry", "electronics", "hardware",
        "department store", "supermarket", "convenience", "gift", "toy",
        "sporting goods", "pet", "florist", "optical", "stationery"
    ],
    SERVICE: [
        "salon", "spa", "gym", "fitness", "studio", "clinic", "dentist",
        "law firm", "accounting", "real estate", "consulting", "agency",
        "beauty", "hair", "nail", "massage", "wellness", "physio", "therapy",
        "cleaning", "maintenance", "repair", "automotive", "veterinary"
    ],
    TECH: [
        "software", "saas", "app", "platform", "startup", "technology",
        "digital", "web", "cloud", "data", "ai", "machine learning",
        "cybersecurity", "devops", "infrastructure", "hosting"
    ],
    INDUSTRIAL: [
        "manufacturing", "warehouse", "logistics", "construction",
        "engineering", "fabrication", "distribution", "supply chain"
    ],
    HEALTHCARE: [
        "doctor", "physician", "hospital", "medical", "health", "dental",
        "pharmacy", "clinic", "urgent care", "surgery", "rehabilitation"
    ],
    ENTERTAINMENT: [
        "cinema", "theater", "museum", "escape room", "bowling", "gaming",
        "amusement", "arcade", "casino", "nightclub", "venue", "concert"
    ]
}

# Search query templates per category
SEARCH_TEMPLATES = {
    FOOD: "{company} menu prices {location}",
    RETAIL: "{company} products prices {location}",
    SERVICE: "{company} services rates {location}",
    TECH: "{company} pricing plans features",
    INDUSTRIAL: "{company} services capabilities {location}",
    HEALTHCARE: "{company} services insurance {location}",
    ENTERTAINMENT: "{company} tickets prices {location}",
    GENERAL: "{company} {location} offerings"
}

# Section inclusion rules per category
SECTION_INCLUSIONS = {
    FOOD: {
        "delivery_analysis": True,
        "menu_pricing": True,
        "seating_capacity": True,
        "opening_hours": True,
        "parking_accessibility": True,
        "table_service": True,
        "happy_hours": True,
        "delivery_partners": True
    },
    RETAIL: {
        "delivery_analysis": False,
        "menu_pricing": False,
        "seating_capacity": False,
        "opening_hours": True,
        "parking_accessibility": True,
        "table_service": False,
        "happy_hours": True,
        "delivery_partners": False
    },
    SERVICE: {
        "delivery_analysis": False,
        "menu_pricing": False,
        "seating_capacity": False,
        "opening_hours": True,
        "parking_accessibility": True,
        "table_service": False,
        "happy_hours": False,
        "delivery_partners": False
    },
    TECH: {
        "delivery_analysis": False,
        "menu_pricing": False,
        "seating_capacity": False,
        "opening_hours": False,  # Online-only
        "parking_accessibility": False,
        "table_service": False,
        "happy_hours": False,
        "delivery_partners": False
    },
    INDUSTRIAL: {
        "delivery_analysis": False,
        "menu_pricing": False,
        "seating_capacity": False,
        "opening_hours": True,
        "parking_accessibility": True,
        "table_service": False,
        "happy_hours": False,
        "delivery_partners": False
    },
    HEALTHCARE: {
        "delivery_analysis": False,
        "menu_pricing": False,
        "seating_capacity": False,
        "opening_hours": True,
        "parking_accessibility": True,
        "table_service": False,
        "happy_hours": False,
        "delivery_partners": False
    },
    ENTERTAINMENT: {
        "delivery_analysis": False,
        "menu_pricing": False,
        "seating_capacity": True,
        "opening_hours": True,
        "parking_accessibility": True,
        "table_service": False,
        "happy_hours": False,
        "delivery_partners": False
    },
    GENERAL: {
        "delivery_analysis": False,
        "menu_pricing": False,
        "seating_capacity": True,
        "opening_hours": True,
        "parking_accessibility": True,
        "table_service": False,
        "happy_hours": False,
        "delivery_partners": False
    }
}

# Terminology substitutions per category
TERMINOLOGY = {
    FOOD: {
        "offering": "menu items",
        "core_offering": "signature dishes",
        "product_line": "food & beverage offerings",
        "service_category": "cuisine type"
    },
    RETAIL: {
        "offering": "products",
        "core_offering": "key products",
        "product_line": "product categories",
        "service_category": "retail category"
    },
    SERVICE: {
        "offering": "services",
        "core_offering": "key services",
        "product_line": "service offerings",
        "service_category": "service type"
    },
    TECH: {
        "offering": "features",
        "core_offering": "key features",
        "product_line": "product suite",
        "service_category": "solution type"
    },
    INDUSTRIAL: {
        "offering": "capabilities",
        "core_offering": "key capabilities",
        "product_line": "service offerings",
        "service_category": "industry sector"
    },
    HEALTHCARE: {
        "offering": "services",
        "core_offering": "specialties",
        "product_line": "medical services",
        "service_category": "specialty area"
    },
    ENTERTAINMENT: {
        "offering": "experiences",
        "core_offering": "attractions",
        "product_line": "entertainment options",
        "service_category": "entertainment type"
    },
    GENERAL: {
        "offering": "offerings",
        "core_offering": "key offerings",
        "product_line": "offerings",
        "service_category": "business type"
    }
}


def classify_business_type(domain: str) -> str:
    """
    Classify business type based on domain string using keyword matching.
    
    Args:
        domain: Business domain string (e.g., "coffee shop", "gym", "software")
    
    Returns:
        Category string (one of FOOD, RETAIL, SERVICE, TECH, INDUSTRIAL, HEALTHCARE, ENTERTAINMENT, GENERAL)
    """
    domain_lower = domain.lower()
    
    # Check each category for keyword matches
    for category, keywords in CATEGORY_KEYWORDS.items():
        for keyword in keywords:
            if keyword in domain_lower:
                logger.debug(f"Classified '{domain}' as '{category}' (matched keyword: '{keyword}')")
                return category
    
    # Default to general if no match
    logger.debug(f"Classified '{domain}' as '{GENERAL}' (no keyword match)")
    return GENERAL


def get_search_template(category: str, company: str, location: str) -> str:
    """
    Get search query template for a specific business category.
    
    Args:
        category: Business category string
        company: Company name
        location: Location string
    
    Returns:
        Search query string with placeholders filled
    """
    template = SEARCH_TEMPLATES.get(category, SEARCH_TEMPLATES[GENERAL])
    return template.format(company=company, location=location)


def get_section_inclusions(category: str) -> Dict[str, bool]:
    """
    Get section inclusion rules for a specific business category.
    
    Args:
        category: Business category string
    
    Returns:
        Dictionary mapping section names to boolean inclusion flags
    """
    return SECTION_INCLUSIONS.get(category, SECTION_INCLUSIONS[GENERAL])


def get_terminology(category: str) -> Dict[str, str]:
    """
    Get terminology substitutions for a specific business category.
    
    Args:
        category: Business category string
    
    Returns:
        Dictionary mapping generic terms to category-specific terms
    """
    return TERMINOLOGY.get(category, TERMINOLOGY[GENERAL])


def apply_terminology(text: str, category: str) -> str:
    """
    Apply terminology substitutions to text based on business category.
    
    Args:
        text: Input text with generic terms
        category: Business category string
    
    Returns:
        Text with category-specific terminology applied
    """
    substitutions = get_terminology(category)
    result = text
    for generic, specific in substitutions.items():
        result = result.replace(generic, specific)
    return result
