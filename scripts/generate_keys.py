#!/usr/bin/env python
"""
Script tạo API key hàng loạt

Usage:
    python scripts/generate_keys.py --tier free --email user@example.com
    python scripts/generate_keys.py --tier premium --count 10 --email bulk@company.com --days 30
    python scripts/generate_keys.py --tier ultra --count 5 --email vip@company.com
"""
import argparse
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()

from services.api_key_service import create_api_key, TierType


def main():
    parser = argparse.ArgumentParser(description="Generate API keys")
    parser.add_argument(
        "--tier",
        required=True,
        choices=["free", "premium", "ultra"],
        help="Tier của key (free/premium/ultra)",
    )
    parser.add_argument(
        "--count",
        type=int,
        default=1,
        help="Số key cần tạo (mặc định: 1)",
    )
    parser.add_argument(
        "--email",
        required=True,
        help="Email chủ sở hữu key",
    )
    parser.add_argument(
        "--days",
        type=int,
        default=None,
        help="Số ngày hợp lệ (để trống = vĩnh viễn)",
    )
    
    args = parser.parse_args()
    
    print(f"Tạo {args.count} key(s) tier '{args.tier}' cho {args.email}...")
    print("-" * 60)
    
    keys = []
    for i in range(args.count):
        try:
            key = create_api_key(
                tier=args.tier,
                owner_email=args.email,
                days_valid=args.days,
            )
            keys.append(key)
            print(f"  [{i+1}] {key}")
        except Exception as e:
            print(f"  [{i+1}] ERROR: {e}")
    
    print("-" * 60)
    print(f"Đã tạo {len(keys)}/{args.count} key(s)")
    
    if args.days:
        print(f"Hết hạn sau: {args.days} ngày")
    else:
        print("Hết hạn: Không (vĩnh viễn)")
    
    print("\n⚠️  LƯU Ý: Key chỉ hiển thị 1 lần này. Hãy lưu lại!")


if __name__ == "__main__":
    main()

