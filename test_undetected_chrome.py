#!/usr/bin/env python3
"""
Test script for undetected-chromedriver with Cisco SharePoint
This will test if undetected-chromedriver can bypass Cisco Duo blocks
"""

import os
import sys
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

print("=" * 60)
print("🧪 Testing undetected-chromedriver with Cisco SharePoint")
print("=" * 60)
print()

# Check if undetected-chromedriver is installed
try:
    import undetected_chromedriver as uc
    print("✅ undetected-chromedriver is installed")
except ImportError:
    print("❌ undetected-chromedriver not found!")
    print()
    print("Installing now...")
    os.system("pip install undetected-chromedriver==3.5.5")
    print()
    print("Please run this script again after installation.")
    sys.exit(1)

# Get SharePoint URL
sharepoint_url = os.getenv('SHAREPOINT_SITE_URL', '')

if not sharepoint_url:
    print("❌ SHAREPOINT_SITE_URL not found in .env file")
    print("Please add: SHAREPOINT_SITE_URL=https://cisco.sharepoint.com/sites/YourSite")
    sys.exit(1)

print(f"📍 SharePoint URL: {sharepoint_url}")
print()

# Launch undetected Chrome
print("🚀 Launching undetected Chrome...")
print("   (This uses your system Chrome with anti-detection patches)")
print()

try:
    # Configure options
    options = uc.ChromeOptions()
    
    # User data directory for persistent session
    user_data_dir = os.path.expanduser('~/.audit-agent-chrome-test')
    options.add_argument(f'--user-data-dir={user_data_dir}')
    
    # Additional stealth options
    options.add_argument('--disable-blink-features=AutomationControlled')
    
    # Launch Chrome
    print("⏳ Opening Chrome browser...")
    driver = uc.Chrome(options=options, version_main=None)
    
    print("✅ Chrome launched successfully!")
    print()
    
    # Navigate to SharePoint
    print(f"🔗 Navigating to SharePoint: {sharepoint_url}")
    driver.get(sharepoint_url)
    
    time.sleep(3)
    
    # Check current URL
    current_url = driver.current_url
    print(f"📍 Current URL: {current_url}")
    print()
    
    # Check if we got blocked by Duo
    if 'duosecurity.com' in current_url:
        print("🔐 Duo Security page detected")
        print()
        
        # Check page content for error messages
        try:
            page_source = driver.page_source.lower()
            
            if 'update required' in page_source or 'browser needs to be updated' in page_source:
                print("❌ BLOCKED: Cisco Duo is requiring browser update")
                print("   'update required' message found on page")
                print()
                print("❌ undetected-chromedriver did NOT bypass Cisco Duo")
                print()
                print("💡 Recommendation: Use Office365 REST API instead (no browser needed)")
            else:
                print("✅ No 'update required' message found!")
                print("🔐 Duo authentication prompt detected")
                print()
                print("📱 ACTION REQUIRED:")
                print("   1. Approve Duo push on your phone")
                print("   2. Complete any additional authentication steps")
                print("   3. Wait for SharePoint to load")
                print()
                print("⏳ Waiting for you to complete authentication...")
                print("   (Script will wait up to 2 minutes)")
                print()
                
                # Wait for authentication
                start_time = time.time()
                while time.time() - start_time < 120:
                    current_url = driver.current_url
                    if 'sharepoint.com' in current_url and 'duosecurity' not in current_url:
                        print("✅ Authentication successful!")
                        print(f"📍 Now on: {current_url}")
                        print()
                        print("✅ undetected-chromedriver BYPASSED Cisco Duo!")
                        print()
                        print("🎉 SUCCESS! You can now use this approach for SharePoint!")
                        break
                    time.sleep(2)
                else:
                    print("⏰ Timeout waiting for authentication")
                    print("   Please complete authentication and check the browser")
                    
        except Exception as e:
            print(f"⚠️  Error checking page: {e}")
    
    elif 'login.microsoftonline.com' in current_url or 'login' in current_url.lower():
        print("🔐 Microsoft/Cisco login page detected")
        print()
        print("📱 ACTION REQUIRED:")
        print("   1. Complete login in the browser")
        print("   2. Approve Duo if prompted")
        print("   3. Wait for SharePoint to load")
        print()
        print("⏳ Waiting for you to complete login (2 minutes)...")
        print()
        
        # Wait for login
        start_time = time.time()
        while time.time() - start_time < 120:
            current_url = driver.current_url
            if 'sharepoint.com' in current_url and 'login' not in current_url.lower():
                print("✅ Login successful!")
                print(f"📍 Now on: {current_url}")
                print()
                print("✅ undetected-chromedriver works with Cisco authentication!")
                print()
                print("🎉 SUCCESS! You can now use this approach for SharePoint!")
                break
            time.sleep(2)
        else:
            print("⏰ Timeout waiting for login")
    
    elif 'sharepoint.com' in current_url:
        print("✅ Already on SharePoint!")
        print("✅ Session was saved from previous login")
        print()
        print("🎉 SUCCESS! undetected-chromedriver works!")
        print()
        print("📋 This means:")
        print("   ✅ Cisco Duo doesn't block this browser")
        print("   ✅ Session persists between runs")
        print("   ✅ You can use this for SharePoint automation")
    
    else:
        print(f"⚠️  Unexpected URL: {current_url}")
    
    print()
    print("=" * 60)
    print("💡 Test Information:")
    print("=" * 60)
    print(f"Browser: undetected-chromedriver (anti-detection)")
    print(f"Session: {user_data_dir}")
    print(f"Current URL: {driver.current_url}")
    print()
    print("Press Enter to close the browser and exit...")
    input()
    
    # Close browser
    driver.quit()
    print()
    print("✅ Test complete!")
    print()
    
    if 'sharepoint.com' in driver.current_url:
        print("🎉 RESULT: undetected-chromedriver WORKS with Cisco!")
        print()
        print("📋 Next steps:")
        print("   1. The agent can now use this approach")
        print("   2. Run: ./QUICK_START.sh")
        print("   3. Try collecting evidence from SharePoint")
    else:
        print("❌ RESULT: undetected-chromedriver was BLOCKED")
        print()
        print("📋 Next steps:")
        print("   1. Use Office365 REST API instead (no browser)")
        print("   2. Or request Cisco IT to allowlist automation")
    
except KeyboardInterrupt:
    print()
    print("⚠️  Test interrupted by user")
    try:
        driver.quit()
    except:
        pass

except Exception as e:
    print(f"❌ Error during test: {e}")
    print()
    import traceback
    traceback.print_exc()
    print()
    print("💡 This might mean:")
    print("   - Chrome is not installed on your system")
    print("   - ChromeDriver version mismatch")
    print("   - Other browser automation issue")
    
    try:
        driver.quit()
    except:
        pass

print()
print("=" * 60)
print("Test script finished")
print("=" * 60)

