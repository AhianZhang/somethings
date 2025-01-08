import sys
import json  # 导入 json 模块以处理配置文件
import markdown
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QTextEdit, QSplitter, QPushButton, QMainWindow, \
    QHBoxLayout, QDialog, QLabel, QLineEdit, QFileDialog
from PyQt5.QtWebEngineWidgets import QWebEngineView
from openai import OpenAI


class ConfigDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("配置 DeepSeek Key")
        self.setGeometry(200, 200, 300, 150)

        # 创建布局
        layout = QVBoxLayout()

        # 添加标签和输入框
        self.label = QLabel("请输入 DeepSeek Key:")
        self.key_input = QLineEdit()
        layout.addWidget(self.label)
        layout.addWidget(self.key_input)

        # 添加保存按钮
        save_button = QPushButton("保存")
        save_button.clicked.connect(self.save_key)
        layout.addWidget(save_button)

        self.setLayout(layout)

        # 加载之前保存的 key
        self.load_key()

    def load_key(self):
        try:
            with open("config.json", "r", encoding='utf-8') as f:
                content = f.read()
                print('loaded: ', content)
                if content.strip():  # 检查文件是否为空
                    config = json.loads(content)
                    print('get key: ', config.get("deepseek_key", ""))
                    self.key_input.setText(config.get("deepseek_key", ""))
                else:
                    print('no key')
        except FileNotFoundError:
            # 如果文件不存在，创建一个空的配置文件
            print('file not found')
            with open("config.json", "w", encoding='utf-8') as f:
                json.dump({"deepseek_key": ""}, f)
        except json.JSONDecodeError:
            # 如果 JSON 格式错误，重置文件
            print('invalid json')

            # with open("config.json", "w", encoding='utf-8') as f:
            #     json.dump({"deepseek_key": ""}, f)
        except Exception as e:
            print(f"加载配置时出错: {e}")

    def save_key(self):
        key = self.key_input.text()
        print(key)
        with open("config.json", "w", encoding='utf-8') as f:  # 使用 UTF-8 编码写入
            json.dump({"deepseek_key": key}, f, ensure_ascii=False)  # 确保写入时不使用 ASCII 编码
        self.accept()  # 关闭对话框


class MarkdownClient(QMainWindow):
    def __init__(self):
        super().__init__()
        self.current_file = None  # 添加当前文件路径记录
        self.deepseek_client = None  # 初始化 DeepSeek 客户端为 None
        self.initUI()
        self.create_deepseek_client()  # 在初始化时创建 DeepSeek 客户端

    def initUI(self):
        # 设置窗口标题和大小
        self.setWindowTitle("somethings")
        self.setGeometry(100, 100, 800, 600)

        # 创建主布局
        main_layout = QVBoxLayout()

        # 创建工具栏
        toolbar = self.addToolBar("工具栏")

        # 添加加载文件按钮
        load_button = QPushButton("加载文件")
        load_button.clicked.connect(self.load_file)
        toolbar.addWidget(load_button)

        # 添加保存文件按钮
        save_button = QPushButton("保存文件")
        save_button.clicked.connect(self.save_file)
        toolbar.addWidget(save_button)

        # 添加设置按钮
        settings_button = QPushButton("设置")
        settings_button.clicked.connect(self.open_settings)
        toolbar.addWidget(settings_button)

        # 创建分割器，用于编辑区
        splitter = QSplitter()
        main_layout.addWidget(splitter)

        # 左侧：Markdown 编辑框
        self.editor = QTextEdit()
        self.editor.textChanged.connect(self.update_preview)
        # 监听文本变化和光标位置变化
        self.editor.textChanged.connect(self.sync_scroll)
        self.editor.cursorPositionChanged.connect(self.sync_scroll)
        splitter.addWidget(self.editor)

        # 右侧：Markdown 预览框
        self.preview = QWebEngineView()
        self.preview.page().loadFinished.connect(self.sync_scroll)  # 添加页面加载完成后的同步
        splitter.addWidget(self.preview)

        # 设置编辑区和预览区的大小相同
        splitter.setSizes([400, 400])  # 可以根据需要调整大小

        # 设置初始内容
        self.editor.setPlainText("")

        # 创建风格优化按钮布局
        style_layout = QHBoxLayout()  # 使用水平布局

        # 添加风格优化按钮
        blog_button = QPushButton("博客风格优化")
        blog_button.clicked.connect(self.optimize_blog_style)
        style_layout.addWidget(blog_button)

        wechat_button = QPushButton("微信风格优化")
        wechat_button.clicked.connect(self.optimize_wechat_style)
        style_layout.addWidget(wechat_button)

        xiaohongshu_button = QPushButton("小红书风格优化")
        xiaohongshu_button.clicked.connect(self.optimize_xiaohongshu_style)
        style_layout.addWidget(xiaohongshu_button)

        freestyle_button = QPushButton("自由生成")
        freestyle_button.clicked.connect(self.optimize_freestyle_style)
        style_layout.addWidget(freestyle_button)

        # 将风格优化按钮布局添加到主布局
        main_layout.addLayout(style_layout)

        # 设置中心小部件
        central_widget = QWidget()
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)

    def update_preview(self):
        # 获取 Markdown 文本
        markdown_text = self.editor.toPlainText()
        # 将 Markdown 转换为 HTML
        html = markdown.markdown(markdown_text)

        # 添加 HTML 头部和样式
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{
                    margin: 20px;
                    font-family: Arial, sans-serif;
                    line-height: 1.6;
                }}
                /* 图片自适应样式 */
                img {{
                    max-width: 100%;
                    height: auto;
                    display: block;
                    margin: 10px auto;
                }}
                /* 针对大图片的处理 */
                .content-wrapper {{
                    max-width: 100%;
                    overflow-x: auto;
                }}
            </style>
        </head>
        <body>
            <div class="content-wrapper">
                {html}
            </div>
        </body>
        </html>
        """

        # 在预览框中显示 HTML
        self.preview.setHtml(html_content)
        # 更新后立即同步滚动位置
        self.sync_scroll()

    def open_settings(self):
        # 打开配置窗口
        config_dialog = ConfigDialog(self)
        config_dialog.exec_()  # 显示对话框并等待关闭

    def create_deepseek_client(self):
        try:
            with open("config.json", "r") as f:
                config = json.load(f)
                deepseek_key = config.get("deepseek_key", "")
                if deepseek_key:
                    # 修改 OpenAI 客户端的初始化方式
                    self.deepseek_client = OpenAI(
                        api_key=deepseek_key,
                        base_url="https://api.deepseek.com",  # 更新 API 地址
                    )
                else:
                    print("未配置 DeepSeek Key，无法创建客户端。")
        except FileNotFoundError:
            print("配置文件未找到，无法创建客户端。")
        except Exception as e:
            print(f"创建 DeepSeek 客户端时出错: {e}")

    def optimize_blog_style(self):
        if not self.deepseek_client:
            print("DeepSeek 客户端未创建，无法进行优化。")
            return

        # 获取当前编辑区的内容
        original_text = self.editor.toPlainText()
        user_playload = {"role": "user", "content": original_text}

        # 调用 DeepSeek 接口进行优化
        self.invoke_ai("你是一个网站博主，擅长编写 SEO 高的博客，要帮我润色现有文章，不要自由扩展", user_playload)

    def invoke_ai(self, desc, user_playload):
        try:
            response = self.deepseek_client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": desc},
                    user_playload
                ],
                stream=False
            )
            optimized_text = response.choices[0].message.content
            # 应用优化后的文本到编辑区
            self.editor.setPlainText(optimized_text)
        except Exception as e:
            print("请求出错:", e)

    def optimize_wechat_style(self):
        # 微信风格优化的逻辑
        if not self.deepseek_client:
            print("DeepSeek 客户端未创建，无法进行优化。")
            return

        # 获取当前编辑区的内容
        original_text = self.editor.toPlainText()
        user_playload = {"role": "user", "content": original_text}

        # 调用 DeepSeek 接口进行优化
        self.invoke_ai("你是一名微信公众号高流量作者，要帮我润色现有文章，不要自由扩展", user_playload)

    def optimize_xiaohongshu_style(self):
        # 小红书风格优化的逻辑
        if not self.deepseek_client:
            print("DeepSeek 客户端未创建，无法进行优化。")
            return

        # 获取当前编辑区的内容
        original_text = self.editor.toPlainText()
        user_playload = {"role": "user", "content": original_text}

        # 调用 DeepSeek 接口进行优化
        self.invoke_ai("你是一名小红书运营，要帮我润色现有文章，不要自由扩展", user_playload)

    def optimize_freestyle_style(self):
        # 自由生成
        if not self.deepseek_client:
            print("DeepSeek 客户端未创建，无法进行优化。")
            return

        # 获取当前编辑区的内容
        original_text = self.editor.toPlainText()
        user_playload = {"role": "user", "content": original_text}

        # 调用 DeepSeek 接口进行优化
        self.invoke_ai("你是一个网文作者，擅长编写高质量的文章，要帮我润色现有文章", user_playload)

    def load_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "选择 Markdown 文件",
            "",
            "Markdown 文件 (*.md);;所有文件 (*.*)"
        )
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as file:
                    content = file.read()
                    self.editor.setPlainText(content)
                    self.current_file = file_path
            except Exception as e:
                print(f"加载文件时出错: {e}")

    def save_file(self):
        if not self.current_file:
            # 如果是第一次保存，打开文件保存对话框
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "保存 Markdown 文件",
                "",
                "Markdown 文件 (*.md);;所有文件 (*.*)"
            )
            if file_path:
                self.current_file = file_path
            else:
                return  # 用户取消保存

        try:
            with open(self.current_file, 'w', encoding='utf-8') as file:
                content = self.editor.toPlainText()
                file.write(content)
        except Exception as e:
            print(f"保存文件时出错: {e}")

    def sync_scroll(self):
        # 获取当前光标所在的块
        cursor = self.editor.textCursor()
        current_block = cursor.block()
        block_position = current_block.position()

        # 计算当前块在整个文档中的相对位置
        total_length = self.editor.document().characterCount()
        if total_length > 0:
            # 使用字符位置而不是块号来计算滚动比例
            scroll_percentage = block_position / total_length

            # 通过 JavaScript 发送滚动消息
            script = f"window.scrollTo(0, document.documentElement.scrollHeight * {scroll_percentage});"
            self.preview.page().runJavaScript(script)

    def restore_scroll(self, position):
        """恢复滚动位置并同步预览窗口"""
        # 恢复滚动位置
        self.editor.verticalScrollBar().setValue(position)
        # 同步预览窗口的滚动
        self.sync_scroll()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    client = MarkdownClient()
    client.show()
    sys.exit(app.exec_())
