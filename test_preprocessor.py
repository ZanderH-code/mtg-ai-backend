#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.preprocessor import preprocess_mtg_query

def test_english_preprocessing():
    """测试英文预处理功能"""
    print("=== 英文预处理测试 ===")
    
    test_cases = [
        ("hate bears", "en"),
        ("bolt test creatures", "en"),
        ("aggro deck dorks", "en"),
        ("combo engine cards", "en"),
        ("evasion creatures", "en"),
        ("removal spells", "en"),
        ("burn spells", "en"),
        ("wrath effects", "en"),
        ("cmc<=3 creatures", "en"),
        ("pow>=4 creatures", "en")
    ]
    
    for input_text, language in test_cases:
        processed = preprocess_mtg_query(input_text, language)
        print(f"输入: {input_text}")
        print(f"输出: {processed}")
        print("-" * 40)

def test_chinese_preprocessing():
    """测试中文预处理功能"""
    print("\n=== 中文预处理测试 ===")
    
    test_cases = [
        ("地落套牌的终端", "zh"),
        ("控制套牌的清场", "zh"),
        ("仇恨熊", "zh"),
        ("快攻小兵", "zh")
    ]
    
    for input_text, language in test_cases:
        processed = preprocess_mtg_query(input_text, language)
        print(f"输入: {input_text}")
        print(f"输出: {processed}")
        print("-" * 40)

if __name__ == "__main__":
    test_english_preprocessing()
    test_chinese_preprocessing()

