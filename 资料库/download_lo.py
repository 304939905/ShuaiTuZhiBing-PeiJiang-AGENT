import requests, os
url = "https://download.documentfoundation.org/libreoffice/stable/26.2.5/win/x86_64/LibreOffice_26.2.5_Win_x86-64.msi"
out = "D:/WorkBuddyData/libreoffice_installer/LibreOffice_26.2.5.msi"
os.makedirs(os.path.dirname(out), exist_ok=True)
print("GET", url, flush=True)
with requests.get(url, stream=True, timeout=600) as r:
    r.raise_for_status()
    total = int(r.headers.get("content-length", 0))
    print("content-length:", total, flush=True)
    done = 0
    with open(out, "wb") as f:
        for chunk in r.iter_content(chunk_size=1024 * 1024):
            if chunk:
                f.write(chunk)
                done += len(chunk)
    print("DONE bytes=", done, "exists=", os.path.exists(out), flush=True)
