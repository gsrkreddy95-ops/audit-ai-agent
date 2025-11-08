import sys
sys.path.insert(0, '.')
from integrations.sharepoint_browser import SharePointBrowserAccess

sp = SharePointBrowserAccess(headless=False)
if sp.connect():
    items = sp.list_folder_contents('TD&R Documentation Train 5/TD&R Evidence Collection/FY2025/XDR Platform/BCR-06.01')
    print(f'\n\n=== EXTRACTED {len(items)} ITEMS ===\n')
    for idx, item in enumerate(items[:3], 1):
        print(f"{idx}. Name: {item['name']}")
        url = item.get('url', '')
        if url:
            print(f"   URL:  {url}")
        else:
            print(f"   URL:  NO URL FOUND")
        print()
    sp.close()
else:
    print("Failed to connect to SharePoint")
