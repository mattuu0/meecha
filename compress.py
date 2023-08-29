import py7zr

files = [
    "privkey.pem",
    "server.crt",
    "requirements.txt",
    "manage.py",
    "commands.txt",
    "compress.py"
]

dirs = [
    "accounts",
    "config",
    "meecha",
    "media_local",
    "static",
    "templates"
]

delete_dirs = [
    "migrations",
    "__pycache__"
]

with py7zr.SevenZipFile("backup.7z","w") as write_sevenzip:
    for file_path in files:
        write_sevenzip.write(file_path,file_path)
    
    for dir_path in dirs:
        write_sevenzip.writeall(dir_path,dir_path)