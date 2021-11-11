from pathlib import Path
import base64
import webbrowser


class HTMLTelegramBot:
    def __init__(self):
        Path("./replay/images").mkdir(parents=True, exist_ok=True)
        self.html_file = open('./replay/index.html', 'w')
        self.write_header()
        self.image_count = 0

    def write_header(self):
        self.html_file.write('''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title></title>
  <link href="style.css" rel="stylesheet" />
</head>
<body>
  <script src="http://ajax.googleapis.com/ajax/libs/jquery/1/jquery.min.js"></script>
  <script>
  </script>
  <table>
    <tbody>
        
''')

    def write_footer(self):
        self.html_file.write('''
        </tbody>
        </table>
</body>
</html>
''')
        url = 'file://' + str(Path(self.html_file.name).absolute())
        self.html_file.flush()
        self.html_file.close()
        webbrowser.open(url, new=2)

    def send_text_message(self, message):
        self.html_file.write('<tr><td>%s</td></tr>\n' % message)

    def send_image_message(self, base64_encoded_image, filename: str = '', caption: str = '',
                           as_document: bool = True):
        f = open('replay/images/image_%d.jpg' % self.image_count, 'wb')
        file_content = base64.b64decode(base64_encoded_image)
        f.write(file_content)
        f.close()
        self.html_file.write(
            '''<tr><td><a href="images/image_%d.jpg">
            <img style="width:300px;height:200px" src="images/image_%d.jpg" /></a></td></tr>\n''' % (
                self.image_count, self.image_count))
        self.image_count = self.image_count + 1
