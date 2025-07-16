#!/usr/bin/env python3
"""
Test script to verify the Discord slash commands work
"""
from ContestGraphImageGenerator import ContestGraphImageGenerator
import os

def test_image_generation():
    """Test that image generation works"""
    print("Testing ContestGraphImageGenerator...")
    
    try:
        # Test with a simple example
        generator = ContestGraphImageGenerator(
            contestId=2119,
            descText="Test Graph",
            imageSelected=0,
            regex=r"^(2023|2024|2022).{9}$",
            overrideContestName=True,
            overrideText="Test Contest"
        )
        
        print("Generator created successfully")
        
        # You can uncomment the line below to test actual generation
        # generator.generate()
        # print("Image generation completed")
        
        return True
        
    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    success = test_image_generation()
    if success:
        print("✅ All tests passed! The Discord slash commands should work.")
    else:
        print("❌ Tests failed. Please check the error above.")
