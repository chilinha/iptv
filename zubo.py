import requests
import os
import re
import datetime

def process_and_save_links(token, url, file_path):
    try:
        if not token:
            print("错误：'token' 未设置，请检查 GitHub Secrets 或 .yml 文件。")
            raise ValueError("Token is not set.")

        full_url = f"{url}?token={token}"
        response = requests.get(full_url)
        response.raise_for_status()

        lines = response.text.splitlines()
        unique_links = set()
        
        pattern = re.compile(r'http[s]?:\/\/(.*?)\/(?:rtp|udp)\/')

        for line in lines:
            match = pattern.search(line)
            if match:
                clean_link = match.group(1)
                unique_links.add(clean_link)
        
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            for link in sorted(list(unique_links)):
                f.write(link + '\n')
        
    except requests.exceptions.RequestException as e:
        print(f"从 {full_url} 下载文件时出错: {e}")
        raise

def update_files_from_templates():
    ip_dir = "ip"
    template_dir = "template"
    final_dir = "zubo"

    os.makedirs(final_dir, exist_ok=True)

    ip_files = os.listdir(ip_dir)

    for filename in ip_files:
        if filename.endswith(".txt"):
            ip_file_path = os.path.join(ip_dir, filename)
            template_file_path = os.path.join(template_dir, filename)
            final_file_path = os.path.join(final_dir, filename)

            print(f"--- 正在处理文件: {filename} ---")

            if not os.path.exists(template_file_path):
                print(f"警告: 找不到对应的模板文件: {template_file_path}，跳过。")
                continue

            try:
                with open(ip_file_path, 'r', encoding='utf-8') as f:
                    ip_links = [line.strip() for line in f if line.strip()]

                if not ip_links:
                    print(f"警告: {ip_file_path} 文件中没有找到链接，跳过。")
                    continue
                
                with open(template_file_path, 'r', encoding='utf-8') as f:
                    template_content = f.read()
                
                current_file_content = ""

                for link in ip_links:
                    replaced_content = template_content.replace("ipipip", link)
                    current_file_content += replaced_content + "\n\n"

                with open(final_file_path, 'w', encoding='utf-8') as f:
                    f.write(current_file_content)

                print(f"文件已成功更新并保存到: {final_file_path}")

            except Exception as e:
                print(f"处理文件 {filename} 时出错: {e}")

def generate_m3u_file(files_to_process):
    zubo_dir = "zubo"
    output_file = "zubo.m3u"
    
    os.makedirs(zubo_dir, exist_ok=True)
    print(f"正在从 '{zubo_dir}' 文件夹生成 '{output_file}' 文件...")

    m3u_content = '#EXTM3U url-tvg="http://e.erw.cc/e.xml"\n'
    current_group = ""

    for url, file_path in files_to_process.items():
        filename = os.path.basename(file_path)
        filepath = os.path.join(zubo_dir, filename)

        if not os.path.exists(filepath):
            print(f"警告: 找不到文件: {filepath}，跳过。")
            continue

        print(f"正在处理文件: {filepath}")
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                lines = [line.strip() for line in f.read().splitlines() if line.strip()]

            for line in lines:
                if line.endswith("#genre#"):
                    parts = line.split(',')
                    if len(parts) > 0:
                        current_group = parts[0].strip()
                    continue
                
                parts = line.split(',')
                if len(parts) >= 2:
                    channel_name = parts[0].strip()
                    url = parts[1].strip()
                    
                    m3u_content += f'#EXTINF:-1 group-title="{current_group}",{channel_name}\n'
                    m3u_content += f'{url}\n'

        except Exception as e:
            print(f"处理文件 {filepath} 时出错: {e}")

    now = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=8)
    current_time = now.strftime("%Y/%m/%d %H:%M")
    m3u_content += f'#EXTINF:-1 group-title="更新时间",{current_time}\n'
    m3u_content += 'http://play.jinnantv.top/live/JNTV1.m3u8\n'
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(m3u_content)

    print(f"\n'{output_file}' 文件已成功生成。")


def main():
    token = os.environ.get('IPTV_TOKEN')

    files_to_process = {
        "https://taoiptv.com/lives/12024.txt": "ip/天津联通.txt",
        "https://taoiptv.com/lives/11024.txt": "ip/北京联通.txt",
        "https://taoiptv.com/lives/37023.txt": "ip/山东电信.txt"
    }

    for base_url, file_path in files_to_process.items():
        process_and_save_links(token, base_url, file_path)
    
    update_files_from_templates()

    generate_m3u_file(files_to_process)


if __name__ == "__main__":
    main()
