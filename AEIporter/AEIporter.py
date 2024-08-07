import sys
from os import path, listdir
from PyQt6.QtWidgets import QApplication, QMainWindow, QLabel, QLineEdit, QPushButton, QCheckBox, QRadioButton, QComboBox, QVBoxLayout, QHBoxLayout, QFileDialog, QMessageBox, QWidget, QButtonGroup
from PyQt6.QtCore import Qt, QMimeData, QRect
from PyQt6.QtGui import QDragEnterEvent, QDropEvent, QPainter, QColor, QBrush, QPen, QFont
from PIL import Image
from AEPi import AEI, CompressionFormat
from AEPi.constants import CompressionFormat
from AEPi.exceptions import UnsupportedCompressionFormatException, AEPiException
from AEPi.codec import compressorFor

class CustomRadioButton(QRadioButton):
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.setFixedSize(88, 30)
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            if self.rect().contains(event.pos()):
                self.setChecked(True)
        super().mousePressEvent(event)
    def paintEvent(self, event):
        on_colour = QColor("#888888")
        painter = QPainter(self)
        indicator_rect = QRect(5, 5, 80, 20)
        if self.isChecked():
            painter.setBrush(QBrush(on_colour))
        else:
            painter.setBrush(QBrush(QColor("#f0f0f0")))
        painter.setPen(QPen(on_colour))
        painter.drawRect(indicator_rect)
        painter.setPen(QColor("black"))
        painter.setFont(QFont("Arial", 11))  # QFont("Xirod", 8)
        text_rect = QRect(indicator_rect.left() + 4, indicator_rect.top() + 2, indicator_rect.width() - 4, indicator_rect.height() - 4)
        painter.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, self.text())


class AEIporterApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("AEIporter - 2024.08.03")
        self.setAcceptDrops(True)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Layouts
        main_layout = QVBoxLayout(central_widget)
        conversion_layout = QHBoxLayout()
        src_layout = QVBoxLayout()
        dest_layout = QHBoxLayout()
        options_layout = QHBoxLayout()
        compression_layout = QHBoxLayout()

        main_layout.addLayout(conversion_layout)
        main_layout.addLayout(src_layout)
        main_layout.addLayout(dest_layout)
        main_layout.addLayout(options_layout)
        main_layout.addLayout(compression_layout)

        # Conversion type selection
        self.folder_var = QCheckBox("Convert Whole Folder")
        conversion_layout.addWidget(self.folder_var)
        
        self.overwrite_var = QCheckBox("Overwrite Existing Files")
        
        self.conversion_var = QButtonGroup(self)
        self.aei_to_png_radio = CustomRadioButton("AEI>PNG")
        self.png_to_aei_radio = CustomRadioButton("PNG>AEI")
        self.aei_to_aei_radio = CustomRadioButton("AEI>AEI")
        self.aei_to_png_radio.setChecked(True)
        
        conversion_layout.addWidget(self.aei_to_png_radio)
        conversion_layout.addWidget(self.png_to_aei_radio)
        conversion_layout.addWidget(self.aei_to_aei_radio)
        
        self.conversion_var.addButton(self.aei_to_png_radio)
        self.conversion_var.addButton(self.png_to_aei_radio)
        self.conversion_var.addButton(self.aei_to_aei_radio)
        
        # Source selection
        self.src_aei_entry = QLineEdit()
        self.src_aei_compression_label = QLabel() 
        self.src_png_entry = QLineEdit()
        self.src_folder_entry = QLineEdit()
        
        src_layout.addWidget(QLabel("Source AEI File Path:"))
        src_layout.addWidget(self.src_aei_entry)
        src_layout.addWidget(self.src_aei_compression_label)
        src_layout.addWidget(QPushButton("Browse", clicked=self.browse_src_aei_file))

        src_layout.addWidget(QLabel("Source PNG File Path:"))
        src_layout.addWidget(self.src_png_entry)
        src_layout.addWidget(QPushButton("Browse", clicked=self.browse_src_png_file))

        src_layout.addWidget(QLabel("Source Folder:"))
        src_layout.addWidget(self.src_folder_entry)
        src_layout.addWidget(QPushButton("Browse", clicked=self.browse_src_folder))

        # Destination selection
        self.dest_folder_entry = QLineEdit()
        dest_layout.addWidget(QLabel("Destination Folder:"))
        dest_layout.addWidget(self.dest_folder_entry)
        dest_layout.addWidget(QPushButton("Browse", clicked=self.browse_dest_folder))
        
        # Options
        options_layout.addWidget(self.overwrite_var)
        self.verbose_var = QCheckBox("Verbose Output")
        options_layout.addWidget(self.verbose_var)
        self.popups_var = QCheckBox("Popups")
        options_layout.addWidget(self.popups_var)

        # Compression format selection
        compression_layout.addWidget(QLabel("Compression Format:"))
        self.compression_var = QComboBox()

        supported_formats = [str(format).split('.')[-1] for format in CompressionFormat.__members__.values() if self.is_compression_supported(format)]
        self.compression_var.addItems(supported_formats)
        compression_layout.addWidget(self.compression_var)

        # Convert button
        convert_button = QPushButton("Convert", clicked=self.convert_files)
        main_layout.addWidget(convert_button)

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent):
        drop_target = self.childAt(event.position().toPoint())
        for url in event.mimeData().urls():
            file_path = url.toLocalFile()
            if file_path.endswith('.aei'):
                self.src_aei_entry.setText(file_path)
                if not self.aei_to_aei_radio.isChecked():
                    self.aei_to_png_radio.setChecked(True)
                self.folder_var.setChecked(False)
                self.display_compression_format(file_path)
            elif file_path.endswith('.png'):
                self.src_png_entry.setText(file_path)
                self.png_to_aei_radio.setChecked(True)
                self.folder_var.setChecked(False)
            elif path.isdir(file_path):
                if drop_target in [self.src_aei_entry, self.src_png_entry, self.src_folder_entry]:
                    self.src_folder_entry.setText(file_path)
                    self.folder_var.setChecked(True)
                else:
                    self.dest_folder_entry.setText(file_path)
                if not self.dest_folder_entry.text():
                    self.dest_folder_entry.setText(file_path)

            if not self.dest_folder_entry.text():
                self.dest_folder_entry.setText(path.dirname(file_path))

    def is_compression_supported(self, compression_format):
        try:
            compressorFor(compression_format)
            return True
        except UnsupportedCompressionFormatException:
            return False

    def show_message(self, title, message, error=False):
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle(title)
        msg_box.setText(message)
        if error:
            msg_box.setIcon(QMessageBox.Icon.Critical)
        else:
            msg_box.setIcon(QMessageBox.Icon.Information)
        msg_box.exec()

    def browse_src_aei_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select AEI File", "", "AEI files (*.aei)")
        if file_path:
            self.src_aei_entry.setText(file_path)
            self.display_compression_format(file_path)
            if not self.dest_folder_entry.text():
                self.dest_folder_entry.setText(path.dirname(file_path))

    def browse_src_png_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select PNG File", "", "PNG files (*.png)")
        if file_path:
            self.src_png_entry.setText(file_path)
            if not self.dest_folder_entry.text():
                self.dest_folder_entry.setText(path.dirname(file_path))

    def browse_src_folder(self):
        folder_path = QFileDialog.getExistingDirectory(self, "Select Source Folder")
        if folder_path:
            self.src_folder_entry.setText(folder_path)
            if not self.dest_folder_entry.text():
                self.dest_folder_entry.setText(folder_path)

    def browse_dest_folder(self):
        folder_path = QFileDialog.getExistingDirectory(self, "Select Destination Folder")
        if folder_path:
            self.dest_folder_entry.setText(folder_path)

    def convert_files(self):
        conversion_type = "AEI to PNG" if self.aei_to_png_radio.isChecked() else "PNG to AEI" if self.png_to_aei_radio.isChecked() else "AEI to AEI"
        is_folder_convert = self.folder_var.isChecked()
        src_aei_file_path = self.src_aei_entry.text()
        src_png_file_path = self.src_png_entry.text()
        src_folder_path = self.src_folder_entry.text()
        dest_folder_path = self.dest_folder_entry.text()
        compression_format = self.compression_var.currentText()
        overwrite = self.overwrite_var.isChecked()
        verbose = self.verbose_var.isChecked()
        popups = self.popups_var.isChecked()
        if not dest_folder_path or not path.isdir(dest_folder_path):
            if popups:
                self.show_message("Error", "Please select a valid destination folder.", error=True)
            print("Please select a valid destination folder.")
            return

        if conversion_type == "AEI to PNG":
            if is_folder_convert:
                if not path.isdir(src_folder_path):
                    if popups:
                        self.show_message("Error", "Invalid source folder path.", error=True)
                    print("Invalid source folder path.")
                    return
                self.convert_folder_to_png(src_folder_path, dest_folder_path, overwrite, verbose)
            else:
                if not path.isfile(src_aei_file_path):
                    if popups:
                        self.show_message("Error", "Invalid AEI file path.", error=True)
                    print("Invalid AEI file path.")
                    return
                if not src_aei_file_path.endswith(".aei"):
                    if popups:
                        self.show_message("Error", "The selected file is not an AEI file.", error=True)
                    print("The selected file is not an AEI file.")
                    return
                self.convert_to_png(src_aei_file_path, dest_folder_path, overwrite, verbose)
        elif conversion_type == "PNG to AEI":
            if is_folder_convert:
                if not path.isdir(src_folder_path):
                    if popups:
                        self.show_message("Error", "Invalid source folder path.", error=True)
                    print("Invalid source folder path.")
                    return
                self.convert_folder_to_aei(src_folder_path, dest_folder_path, compression_format, overwrite, verbose)
            else:
                if not path.isfile(src_png_file_path):
                    if popups:
                        self.show_message("Error", "Invalid PNG file path.", error=True)
                    print("Invalid PNG file path.")
                    return
                if not src_png_file_path.endswith(".png"):
                    if popups:
                        self.show_message("Error", "The selected file is not a PNG file.", error=True)
                    print("The selected file is not a PNG file.")
                    return
                self.convert_to_aei(src_png_file_path, dest_folder_path, compression_format, overwrite, verbose)
        else:  # AEI to AEI
            if is_folder_convert:
                if not path.isdir(src_folder_path):
                    if popups:
                        self.show_message("Error", "Invalid source folder path.", error=True)
                    print("Invalid source folder path.")
                    return
                self.convert_folder_to_aei(src_folder_path, dest_folder_path, compression_format, overwrite, verbose, is_aei_to_aei=True)
            else:
                if not path.isfile(src_aei_file_path):
                    if popups:
                        self.show_message("Error", "Invalid AEI file path.", error=True)
                    print("Invalid AEI file path.")
                    return
                if not src_aei_file_path.endswith(".aei"):
                    if popups:
                        self.show_message("Error", "The selected file is not an AEI file.", error=True)
                    print("The selected file is not an AEI file.")
                    return
                self.convert_to_aei(src_aei_file_path, dest_folder_path, compression_format, overwrite, verbose, is_aei_to_aei=True)
        
        if popups:
            self.show_message("Info", "Conversion over.")
        print("Conversion over.")

    def convert_to_aei(self, file_path, dest_folder_path, compression_format, overwrite=False, verbose=False, popups=False, counter=0, is_aei_to_aei=False):
        try:
            compression_format_enum = getattr(CompressionFormat, compression_format)
        except AttributeError:
            if popups:
                self.show_message("Error", "Invalid compression format.", error=True)
            print("Invalid compression format.")
            return -1

        if not path.isfile(file_path):
            if popups:
                self.show_message("Error", "Invalid file path.", error=True)
            print("Invalid file path.")
            return -1

        if is_aei_to_aei:
            try:
                with AEI.read(file_path) as aei:
                    aei_file_path = path.join(dest_folder_path, path.splitext(path.basename(file_path))[0] + f"_{compression_format}.aei")
                    if not overwrite and path.exists(aei_file_path):
                        if verbose:
                            print(f"Skipping {path.basename(file_path)} (File already exists).")
                        return counter
                    with open(aei_file_path, "wb") as dest_f:
                        aei.write(dest_f, format=compression_format_enum)
                    counter += 1
                    if verbose:
                        print(f"Converted {path.basename(file_path)} to {path.basename(aei_file_path)} with compression format {compression_format}")
            except Exception as e:
                if popups:
                    self.show_message("Error", f"Failed to convert AEI: {str(e)}", error=True)
                print(f"Failed to convert AEI: {str(e)}")
                return -1
        else:
            try:
                with Image.open(file_path) as png_image:
                    with AEI(png_image) as new_aei:
                        aei_file_path = path.join(dest_folder_path, path.splitext(path.basename(file_path))[0] + f"_{compression_format}.aei")
                        if not overwrite and path.exists(aei_file_path):
                            if verbose:
                                print(f"Skipping {path.basename(file_path)} (AEI file already exists).")
                            return counter
                        with open(aei_file_path, "wb") as aei_file:
                            new_aei.write(aei_file, format=compression_format_enum)
                        counter += 1
                        if verbose:
                            print(f"Converted {path.basename(file_path)} to {path.basename(aei_file_path)} with compression format {compression_format}")
            except Exception as e:
                if popups:
                    self.show_message("Error", f"Failed to convert PNG to AEI: {str(e)}", error=True)
                print(f"Failed to convert PNG to AEI: {str(e)}")
                return -1
        return counter
        
    def convert_to_png(self, aei_file_path, dest_folder_path, overwrite=False, verbose=False, popups=False, whole_image=True, counter=0):
        if not path.isfile(aei_file_path):
            if popups:
                self.show_message("Error", "Invalid AEI file path.", error=True)
            print("Invalid AEI file path.")
            return

        try:
            aei = AEI.read(aei_file_path)
        except AEPiException as ex:
            if popups:
                self.show_message("Error", f"Failed to read {aei_file_path} with {type(ex).__name__}: '{ex}'", error=True)
            print(f"Failed to read {aei_file_path} with {type(ex).__name__}: '{ex}'")
            return -1

        with aei:
            if whole_image:
                png_file_name = f"{path.splitext(path.basename(aei_file_path))[0]}.png"
                png_file_path = path.join(dest_folder_path, png_file_name)
                if not overwrite and path.exists(png_file_path):
                    if verbose:
                        print(f"Skipping {png_file_name} (File already exists).")
                else:
                    aei._image.save(png_file_path)
                    counter += 1
                    if verbose:
                        print(f"Converted {path.basename(aei_file_path)} to {png_file_name}")
            else:
                for i, tex in enumerate(aei.textures):
                    with aei.getTexture(tex) as im:
                        png_file_name = f"{path.splitext(path.basename(aei_file_path))[0]}_{i}.png"
                        png_file_path = path.join(dest_folder_path, png_file_name)
                        if not overwrite and path.exists(png_file_path):
                            if verbose:
                                print(f"Skipping {png_file_name} (File already exists).")
                            continue
                        im.save(png_file_path)
                        counter += 1
                        if verbose:
                            print(f"Converted texture {i} of {path.basename(aei_file_path)} to {png_file_name}")
        return counter

    def convert_folder_to_aei(self, src_folder_path, dest_folder_path, compression_format, overwrite=False, verbose=False, popups=False, is_aei_to_aei=False):
        if not path.isdir(src_folder_path):
            if popups:
                self.show_message("Error", "Invalid source PNGs' folder path.", error=True)
            print("Invalid source PNG folder path.")
            return

        file_counter = 0
        ext = '.aei' if is_aei_to_aei else '.png'
        for filename in listdir(src_folder_path):
            if filename.lower().endswith(ext):
                png_file_path = path.join(src_folder_path, filename)
                file_counter = self.convert_to_aei(png_file_path, dest_folder_path, compression_format, overwrite=overwrite, verbose=verbose, popups=popups, counter=file_counter, is_aei_to_aei=is_aei_to_aei)
        if popups:
            self.show_message("Info", f"Converted PNG to AEI in count of {file_counter}.")
        if verbose:
            if is_aei_to_aei:
                print(f"Converting {file_counter}x AEI2AEI over.")
            else:
                print(f"Converting {file_counter}x PNG2AEI over.")

    def convert_folder_to_png(self, src_folder_path, dest_folder_path, overwrite=False, verbose=False, popups=False):
        if not path.isdir(src_folder_path):
            if popups:
                self.show_message("Error", "Invalid source AEIs' folder path.", error=True)
            print("Invalid source AEI folder path.")
            return

        file_counter = 0
        for filename in listdir(src_folder_path):
            if filename.lower().endswith('.aei'):
                aei_file_path = path.join(src_folder_path, filename)
                file_counter = self.convert_to_png(aei_file_path, dest_folder_path, overwrite=overwrite, verbose=verbose, popups=popups, counter=file_counter)
        if popups:
            self.show_message("Info", f"Converted AEI to PNG in count of {file_counter}.")
        if verbose:
            print(f"Converting AEI2PNG {file_counter}x over.")
            
    def display_compression_format(self, file_path):
        try:
            with open(file_path, "rb") as f:
                f.seek(8)  
                compression_byte = f.read(1)
                compression_id = int.from_bytes(compression_byte, "little")
                compression_format, mipmapped = CompressionFormat.fromBinary(compression_id)
                self.src_aei_compression_label.setText(f"Format: {compression_format.name}")
        except Exception as e:
            self.src_aei_compression_label.setText("Format: Unknown")
            print(f"Failed to read compression format: {e}")


def _runGui():
    app = QApplication(sys.argv)
    window = AEIporterApp()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    _runGui()
