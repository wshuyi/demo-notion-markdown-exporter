import streamlit as st
import base64
import shutil
from zipfile import ZipFile
from pathlib import Path
import notion
import os
from notion.client import NotionClient
import requests
import sys
from exporter import PageBlockExporter

def export_cli(token_v2,url):
    if not(os.path.isdir(directory)):
        os.makedirs(os.path.join(directory))
    
    client=NotionClient(token_v2=token_v2)
    url=url
    
    exporter = PageBlockExporter(url,client)
    exporter.create_main_folder(directory)
    exporter.create_file()
    export(exporter)

def export(exporter):
    """Recursively export page block with its sub pages
    
        Args:
            exporter(PageBlockExporter()): export page block
    """
    exporter.page2md(tapped = 0)
    try:
        exporter.write_file()
    except:
        st.markdown(f"Error exporting {exporter.title}.md!")
    for sub_exporter in exporter.sub_exporters:
        export(sub_exporter)

def zipdir(path, ziph):
    # ziph is zipfile handle
    for root, dirs, files in os.walk(path):
        for file in files:
            ziph.write(os.path.join(root, file))

# main proc starts here
st.title("Notion Markdown Exporter")
st.markdown("This Web app is developed by [Shuyi Wang](https://twitter.com/wshuyi) based on [Eunchan Cho(@echo724)\'s notion2md](https://github.com/echo724/notion2md)")
st.markdown("The coressponding [Github Page of this app is here](https://github.com/wshuyi/demo-notion-markdown-exporter).")


token_v2 = st.text_input("Your Notion token_v2:")
url = st.text_input("The Link or ID you want to export:")

running = False

directory='./notion_output/'

if token_v2 and url and not running:
    if st.button("export"):
        running = True

        if Path(directory).exists():
            shutil.rmtree(Path(directory))
        export_cli(token_v2, url)
        with ZipFile('exported.zip', 'w') as myzip:
            zipdir(directory, myzip)
        with open('exported.zip', "rb") as f:
            bytes = f.read()
            b64 = base64.b64encode(bytes).decode()
            href = f'<a href="data:file/zip;base64,{b64}" download=\'exported.zip\'>\
                Click to download\
            </a>'
        st.markdown(href, unsafe_allow_html=True)
        running = False
