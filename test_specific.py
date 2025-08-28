#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.preprocessor import preprocess_mtg_query

def test_blue_instant_sorcery():
    """测试蓝色瞬间法术的预处理"""
    print("=== 测试：蓝色瞬间法术 ===")
    
    test_cases = [
        "蓝色瞬间法术",
        "瞬间蓝色法术", 
        "法术蓝色瞬间",
        "蓝色瞬间法术卡",
        "红色瞬间",
        "蓝色法术"
    ]
    
    for input_text in test_cases:
        processed = preprocess_mtg_query(input_text, "zh")
        print(f"输入: {input_text}")
        print(f"输出: {processed}")
        print("-" * 40)

if __name__ == "__main__":
    test_blue_instant_sorcery()
