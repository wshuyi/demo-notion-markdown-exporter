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

def recursive_getblocks(block,container,client):
    new_id = client.get_block(block.id)
    if not new_id in container:
        container.append(new_id)
        try:
            for children_id in block.get("content"):
                children = client.get_block(children_id)
                recursive_getblocks(children,container,client)
        except:
            return

def link(name,url):
    return "["+name+"]"+"("+url+")"

def image_export(url,count,directory):
    img_dir = directory + 'img_{0}.png'.format(count)
    r = requests.get(url, allow_redirects=True)
    open(img_dir,'wb').write(r.content)
    return img_dir

def block2md(blocks,directory):
    md = ""
    img_count = 0
    numbered_list_index = 0
    title = blocks[0].title
    title = title.replace(' ','')
    directory += '{0}/'.format(title)
    if not(os.path.isdir(directory)):
        Path(directory).mkdir()
    for block in blocks:
        try:
            btype = block.type
        except:
            continue
        if btype != "numbered_list":
            numbered_list_index = 0
        try:
            bt = block.title
        except:
            pass
        if btype == 'header':
            md += "# " + bt
        elif btype == "sub_header":
            md += "## " +bt
        elif btype == "sub_sub_header":
            md += "### " +bt
        elif btype == 'page':
            try:
                if "https:" in block.icon:
                    icon = "!"+link("",block.icon)
                else:
                    icon = block.icon
                md += "# " + icon + bt
            except:
                md += "# " + bt
        elif btype == 'text':
            md += bt +"  "
        elif btype == 'bookmark':
            md += link(bt,block.link)
        elif btype == "video" or btype == "file" or btype =="audio" or btype =="pdf" or btype == "gist":
            md += link(block.source,block.source)
        elif btype == "bulleted_list" or btype == "toggle":
            md += '- '+bt
        elif btype == "numbered_list":
            numbered_list_index += 1
            md += str(numbered_list_index)+'. ' + bt
        elif btype == "image":
            img_count += 1
            try:
                img_dir = image_export(block.source,img_count,directory)
                md += "!"+link(img_dir,img_dir)
            except:
                # pass
                st.markdown(f"error exporting {block.source}")
        elif btype == "code":
            md += "```"+block.language+"\n"+block.title+"\n```"
        elif btype == "equation":
            md += "$$"+block.latex+"$$"
        elif btype == "divider":
            md += "---"
        elif btype == "to_do":
            if block.checked:
                md += "- [x] "+ bt
            else:
                md += "- [ ]" + bt
        elif btype == "quote":
            md += "> "+bt
        elif btype == "column" or btype =="column_list":
            continue
        else:
            pass
        md += "\n\n"
    return md

def export(url,token):
    client = NotionClient(token_v2=token)
    page = client.get_block(url)
    blocks = []
    recursive_getblocks(page,blocks,client)
    md = block2md(blocks,'./')
    return md

def export_cli(fname, directory, token_v2, url):
    fname = os.path.join(directory,fname)
    file = open(fname,'w')
    blocks = []

    client = NotionClient(token_v2 = token_v2)
    page = client.get_block(url)

    recursive_getblocks(page,blocks,client)
    md = block2md(blocks,directory)

    file.write(md)
    file.close()

def notion_markdown_export(token_v2, url, directory):
    pages_to_download = []

    client = NotionClient(token_v2 = token_v2)
    page = client.get_block(url)

    for children_id in page.get("content"):
        children = client.get_block(children_id)
        if children.title:
            pages_to_download.append({"title":children.title, "id":children.id})
    
    if not(os.path.isdir(directory)):
        Path(directory).mkdir()
    
    for item in pages_to_download:
        try:
            export_cli(f"{item['title']}.md", directory, token_v2, item["id"])
        except:
            st.markdown(f"Error exporting {item['title']}.md!")
    return 

def adjust_notion_image_dir(source_md):
    with open(source_md) as f:
        data = f.read()
    data = data.replace("./notion_output/", "")
    with open(source_md, 'w') as f:
        f.write(data)

def batch_adjust_notion_image_dir(directory):
    source_mds = list(Path(directory).glob("*.md"))
    for source_md in source_mds:
        adjust_notion_image_dir(source_md)

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

directory = './notion_output/'

running = False

if token_v2 and url and not running:
    if st.button("export"):
        running = True
        notion_markdown_export(token_v2, url, directory)
        batch_adjust_notion_image_dir(directory)
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
