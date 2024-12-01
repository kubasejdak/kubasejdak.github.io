from datetime import datetime
import os
import shutil

def add_asset_redirect(config, asset_path, asset_url):
    # Define paths.
    source_path = os.path.join(config["docs_dir"], "assets", asset_path)
    file_name = os.path.basename(asset_path)
    
    # The file will be served from /downloads/<file_name>.
    destination_dir = os.path.join(config["site_dir"], "downloads")
    destination_path = os.path.join(destination_dir, file_name)

    # Ensure the /downloads directory exists.
    os.makedirs(destination_dir, exist_ok=True)

    # Copy the asset from docs/assets to the /downloads directory in the site folder.
    if os.path.exists(source_path):
        shutil.copy(source_path, destination_path)
    else:
        print(f"{asset_path} not found at {source_path}")

    # Create a JavaScript-based redirect page at the user-defined URL.
    redirect_dir = os.path.join(config["site_dir"], asset_url.strip("/"))
    os.makedirs(redirect_dir, exist_ok=True)

    index_path = os.path.join(redirect_dir, "index.html")
    with open(index_path, "w") as f:
        f.write(f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta http-equiv="refresh" content="0;url=/downloads/{file_name}">
    <title>Redirecting...</title>
    <script type="text/javascript">
        window.location.href = '/downloads/{file_name}';
    </script>
</head>
<body>
    <p>If you are not redirected automatically, <a href="/downloads/{file_name}">click here to download the asset</a>.</p>
</body>
</html>""")

    print(f"Created asset redirect from {asset_url} to /downloads/{file_name}")

def on_config(config, **kwargs):
    config.copyright = f"Copyright © 2024 - {datetime.now().year} Kuba Sejdak"

def on_post_build(config, **kwargs):
    add_asset_redirect(config, "JakubSejdak_CV.pdf", "/cv")
