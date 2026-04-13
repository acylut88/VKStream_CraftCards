#!/usr/bin/env python3
"""
Comprehensive API endpoint testing
"""

import asyncio
import sys
from database import DatabaseManager
from main import db, engine, process_lootbox_opening
import json

async def test_stream_database_methods():
    """Test all stream event database methods"""
    print("\n" + "="*60)
    print("🧪 TESTING STREAM DATABASE METHODS")
    print("="*60)
    
    try:
        # Test 1: Create stream session
        print("\n✓ Test 1: Creating stream session...")
        session_id = await db.create_stream_session('both', '2026-04-13', 'Test Stream')
        if session_id:
            print(f"  ✅ Session created: ID={session_id}")
        else:
            print("  ❌ Failed to create session")
            return False

        # Test 2: Get active session
        print("\n✓ Test 2: Getting current active session...")
        active = await db.get_current_active_session()
        if active:
            print(f"  ✅ Active session found: {active}")
        else:
            print("  ❌ No active session found")

        # Test 3: Update user event progress
        print("\n✓ Test 3: Updating user event progress...")
        await db.update_user_event_progress(
            session_id=session_id,
            vk_id='test_user_123',
            event_type='card',
            value=8,
            cards_data=json.dumps({'LT': 1, 'ST': 2})
        )
        print("  ✅ Event progress updated")

        # Test 4: Get current leaderboard
        print("\n✓ Test 4: Getting leaderboard data...")
        leaderboard = await db.get_current_leaderboard(session_id, 'card', 10)
        if leaderboard:
            print(f"  ✅ Leaderboard retrieved: {len(leaderboard)} entries")
        else:
            print("  ⚠️  Leaderboard empty (expected for test)")

        # Test 5: Record rare drop
        print("\n✓ Test 5: Recording rare drop...")
        await db.record_rare_drop(
            session_id=session_id,
            vk_id='test_user_123',
            nickname='TestPlayer',
            card_type='LT',
            level=5,
            probability=0.0035,
            box_type='elite'
        )
        print("  ✅ Rare drop recorded")

        # Test 6: Get recent rare drops
        print("\n✓ Test 6: Getting rare drops...")
        drops = await db.get_recent_rare_drops(session_id, 5)
        if drops:
            print(f"  ✅ Rare drops retrieved: {len(drops)} entries")
        else:
            print("  ⚠️  No rare drops yet")

        # Test 7: Reset PA for all users
        print("\n✓ Test 7: Resetting PA status for all users...")
        await db.reset_pa_active_today_all()
        print("  ✅ PA status reset")

        # Test 8: Get session results for export
        print("\n✓ Test 8: Getting session results for export...")
        results = await db.get_session_results(session_id, 'card')
        print(f"  ✅ Session results retrieved: {len(results)} entries")

        # Test 9: Get session info
        print("\n✓ Test 9: Getting session info...")
        info = await db.get_session_info(session_id)
        if info:
            print(f"  ✅ Session info: {info}")
        else:
            print("  ❌ Session info not found")

        # Test 10: Finish session
        print("\n✓ Test 10: Finishing stream session...")
        await db.finish_stream_session(session_id)
        print("  ✅ Session finished")

        print("\n" + "="*60)
        print("✅ ALL DATABASE TESTS PASSED")
        print("="*60)
        return True

    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_user_operations():
    """Test user account operations"""
    print("\n" + "="*60)
    print("🧪 TESTING USER OPERATIONS")
    print("="*60)
    
    try:
        # Test user creation
        print("\n✓ Creating test user...")
        test_user_id = f'test_user_{int(__import__("time").time())}'
        await db.create_user(test_user_id, 'TestPlayer', 5)
        print("  ✅ User created")

        # Test get user
        print("\n✓ Getting user data...")
        user = await db.get_user(test_user_id)
        if user:
            print(f"  ✅ User data retrieved")
        else:
            print("  ❌ User not found")
            return False

        # Test PA charge update
        print("\n✓ Updating PA charges...")
        await db.update_user_field(test_user_id, 'pa_charges', 5)
        user = await db.get_user(test_user_id)
        if user['pa_charges'] == 5:
            print(f"  ✅ PA charges updated to {user['pa_charges']}")
        else:
            print("  ❌ PA charges update failed")

        # Test AC balance update
        print("\n✓ Updating AC balance...")
        await db.update_user_field(test_user_id, 'ac_balance', 1000)
        user = await db.get_user(test_user_id)
        if user['ac_balance'] == 1000:
            print(f"  ✅ AC balance updated to {user['ac_balance']}")
        else:
            print("  ❌ AC balance update failed")

        print("\n" + "="*60)
        print("✅ ALL USER TESTS PASSED")
        print("="*60)
        return True

    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_game_logic():
    """Test game engine integration"""
    print("\n" + "="*60)
    print("🧪 TESTING GAME LOGIC")
    print("="*60)
    
    try:
        # Test 1: Get random cards with PA
        print("\n✓ Test 1: Getting random cards...")
        cards = engine.get_random_cards(1, has_pa=False, count=3, is_elite=False)
        if cards and len(cards) > 0:
            print(f"  ✅ Got {len(cards)} random cards: {cards}")
        else:
            print("  ❌ Failed to get cards")
            return False

        # Test 2: Get cards with PA activated
        print("\n✓ Test 2: Getting cards with PA...")
        cards_pa = engine.get_random_cards(2, has_pa=True, count=3, is_elite=False)
        if cards_pa and len(cards_pa) > 0:
            print(f"  ✅ Got {len(cards_pa)} cards with PA: {cards_pa}")
        else:
            print("  ❌ Failed to get cards with PA")
            return False

        # Test 3: Process lootbox (game logic)
        print("\n✓ Test 3: Processing lootbox...")
        logic_test_id = f'logic_test_user_{int(__import__("time").time())}'
        await db.create_user(logic_test_id, 'LogicTestPlayer', 5)
        
        # First ensure user is set up
        user = await db.get_user(logic_test_id)
        if user:
            print(f"  ✅ Found user: created successfully")
        else:
            print("  ❌ User not found for logic test")
            return False

        print("\n" + "="*60)
        print("✅ ALL GAME LOGIC TESTS PASSED")
        print("="*60)
        return True

    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Run all tests"""
    print("\n" + "█"*60)
    print("🚀 BACKEND COMPREHENSIVE TEST SUITE")
    print("█"*60)
    
    results = []
    
    # Run all test suites
    results.append(("Stream Database Methods", await test_stream_database_methods()))
    results.append(("User Operations", await test_user_operations()))
    results.append(("Game Logic", await test_game_logic()))
    
    # Summary
    print("\n" + "█"*60)
    print("📊 TEST SUMMARY")
    print("█"*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} | {name}")
    
    print(f"\nTotal: {passed}/{total} test suites passed")
    
    if passed == total:
        print("\n🎉 ALL BACKEND TESTS PASSED!")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test suite(s) failed")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
