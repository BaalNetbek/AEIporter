from os import path
from os import listdir
import tkinter as tk
from tkinter import filedialog, messagebox, OptionMenu
from PIL import Image
from AEPi import AEI, CompressionFormat
from AEPi.constants import CompressionFormat
from AEPi.exceptions import UnsupportedCompressionFormatException
from AEPi.exceptions import AEPiException
from AEPi.codec import compressorFor
from tkinterdnd2 import DND_FILES, TkinterDnD

def convert_to_aei(png_file_path, dest_folder_path, compression_format, overwrite=False, verbose=False, silent=False, counter=0):
    try:
        compression_format_enum = getattr(CompressionFormat, compression_format)
    except AttributeError:
        if silent == False: messagebox.showerror("Error", "Invalid compression format.")
        print("Invalid compression format.")
        return -1

    if not path.isfile(png_file_path):
        if silent == False: messagebox.showerror("Error", "Invalid PNG file path.")
        print("Invalid PNG file path.")
        return -1

    # Open the PNG file
    with Image.open(png_file_path) as png_image:
        # Create a new AEI file
        with AEI(png_image) as new_aei:
            aei_file_path = path.join(dest_folder_path, path.splitext(path.basename(png_file_path))[0] + ".aei")
            # Check if the file already exists and overwrite is not enabled
            if not overwrite and path.exists(aei_file_path):
                if verbose:
                    print(f"Skipping {path.basename(png_file_path)} (AEI file already exists).")
                return 0
            # Write the AEI file to disk
            with open(aei_file_path, "wb") as aei_file:
                # Write in specified compression format
                new_aei.write(aei_file, format=compression_format_enum)
            counter += 1
            if verbose:
                print(f"Converted {path.basename(png_file_path)} to {path.basename(aei_file_path)}")
                
    return counter
    
def convert_to_png(aei_file_path, dest_folder_path, overwrite=False, verbose=False, silent=False, counter=0):
    if not path.isfile(aei_file_path):
        if silent == False: messagebox.showerror("Error", "Invalid AEI file path.")
        print("Invalid AEI file path.")
        return
    
    
    # Read the AEI file
    try:
        aei = AEI.read(aei_file_path)
    except AEPiException as ex:
        if silent == False: messagebox.showerror("Error",f"Failed to read {aei_file_path} with {type(ex).__name__}: '{ex}'")
        print(f"Failed to read {aei_file_path} with {type(ex).__name__}: '{ex}'")
        return -1
    with aei:
        # Iterate through textures
        for i, tex in enumerate(aei.textures):
            # Get texture as Pillow Image
            with aei.getTexture(tex) as im:
                # Construct PNG file path using AEI file name
                png_file_name = f"{path.splitext(path.basename(aei_file_path))[0]}_{i}.png"
                png_file_path = path.join(dest_folder_path, png_file_name)
                # Check if file exists and overwrite is not enabled
                if not overwrite and path.exists(png_file_path):
                    if verbose:
                        print(f"Skipping {png_file_name} (File already exists).")
                    continue 
                # Save the texture as PNG
                im.save(png_file_path)
                counter += 1
                if verbose:
                    print(f"Converted texture {i} of {path.basename(aei_file_path)} to {png_file_name}")
    return counter
    
def convert_folder_to_aei(src_folder_path, dest_folder_path, compression_format, overwrite=False, verbose=False, silent=False):
    if not path.isdir(src_folder_path):
        if silent == False: messagebox.showerror("Error", "Invalid source PNGs' folder path.")
        print("Invalid source PNG folder path.")
        return
    
    file_counter = 0 
    for filename in listdir(src_folder_path):
        if filename.lower().endswith('.png'):
            # Construct paths for PNG and AEI files
            png_file_path = path.join(src_folder_path, filename)
          #  aei_file_name = f"{path.splitext(filename)[0]}.aei"
          #  aei_file_path = path.join(dest_folder_path, aei_file_name)
        
            # Convert each PNG file to AEI, update converted files counter
            file_counter = convert_to_aei(png_file_path, dest_folder_path, compression_format, overwrite=overwrite, verbose=verbose, silent=silent, counter=file_counter)
    if silent == False:
        if verbose: messagebox.showinfo("Info", f"Coverted PNG to AEI in count of {file_counter}.\nScr: {src_folder_path}\nDst: {dest_folder_path}")
        else: messagebox.showinfo("Info", f"Coverted PNG to AEI in count of {file_counter}.")
    if verbose: print(f"Converting {file_counter}x PNG2AEI over.")


def convert_folder_to_png(src_folder_path, dest_folder_path, overwrite=False, verbose=False, silent=False):
    if not path.isdir(src_folder_path):
        if silent == False: messagebox.showerror("Error", "Invalid source AEIs' folder path.")
        print("Invalid source AEI folder path.")
        return
    file_counter = 0    
    for filename in listdir(src_folder_path):
        if filename.lower().endswith('.aei'):
            aei_file_path = path.join(src_folder_path, filename)
            file_counter = convert_to_png(aei_file_path, dest_folder_path, overwrite=overwrite, verbose=verbose, silent=silent, counter=file_counter)
    if silent == False:
        if verbose: messagebox.showinfo("Info", f"Coverted AEI to PNG in count of {file_counter}.\n\nScr: {src_folder_path}\n\nDst: {dest_folder_path}")
        else: messagebox.showinfo("Info", f"Coverted AEI to PNG in count of {file_counter}.")
    if verbose: print(f"Converting AEI2PNG {file_counter}x over.")

def convert_files():
    conversion_type = conversion_var.get()
    is_folder_convert = folder_var.get()
    src_aei_file_path = src_aei_entry.get()
    src_png_file_path = src_png_entry.get()
    src_folder_path = src_folder_entry.get()
    dest_folder_path = dest_folder_entry.get()
    compression_format = compression_var.get()
    overwrite = overwrite_var.get()
    verbose = verbose_var.get()
    silent = silent_var.get()
    
    if not dest_folder_path or not path.isdir(dest_folder_path):
        if silent == False: messagebox.showerror("Error", "Please select a valid destination folder.")
        print("Please select a valid destination folder.")
        return

    if conversion_type == "AEI to PNG":
        if is_folder_convert:
            if not path.isdir(src_folder_path):
                if silent == False: messagebox.showerror("Error", "Invalid source folder path.")
                print("Invalid source folder path.")
                return
            convert_folder_to_png(src_folder_path, dest_folder_path, overwrite=overwrite, verbose=verbose)
        else:
            if not path.isfile(src_aei_file_path):
                if silent == False: messagebox.showerror("Error", "Invalid AEI file path.")
                print("Invalid AEI file path.")
                return
            # Check if the file is a valid AEI file
            if not src_aei_file_path.endswith(".aei"):
                if silent == False: messagebox.showerror("Error", "The selected file is not an AEI file.")
                print("The selected file is not an AEI file.")
                return
            convert_to_png(src_aei_file_path, dest_folder_path, overwrite=overwrite, verbose=verbose)
    else:  # PNG to AEI
        if is_folder_convert:
            if not path.isdir(src_folder_path):
                if silent == False: messagebox.showerror("Error", "Invalid source folder path.")
                print("Invalid source folder path.")
                return
            convert_folder_to_aei(src_folder_path, dest_folder_path, compression_format, overwrite=overwrite, verbose=verbose)
        else:
            if not path.isfile(src_png_file_path):
                if silent == False: messagebox.showerror("Error", "Invalid PNG file path.")
                print("Invalid PNG file path.")
                return
            # Check if the file is a valid PNG file
            if not src_png_file_path.endswith(".png"):
                if silent == False: messagebox.showerror("Error", "The selected file is not a PNG file.")
                print("The selected file is not a PNG file.")
                return
            convert_to_aei(src_png_file_path, dest_folder_path, compression_format, overwrite=overwrite, verbose=verbose)
    
    if silent == False: messagebox.showinfo("Info", "Conversion over.")
    print("Conversion over.")

def browse_src_aei_file(event=None):
    if event and event.data:
        file_path = event.data.strip('{}')
    else:
        file_path = filedialog.askopenfilename(filetypes=[("AEI files", "*.aei")])
    if file_path:
        src_aei_entry.delete(0, tk.END)
        src_aei_entry.insert(0, file_path)
        if not dest_folder_entry.get():
            dest_folder_entry.insert(0, path.dirname(file_path))

def browse_src_png_file(event=None):
    if event and event.data:
        file_path = event.data.strip('{}')
    else:
        file_path = filedialog.askopenfilename(filetypes=[("PNG files", "*.png")])
    if file_path:
        src_png_entry.delete(0, tk.END)
        src_png_entry.insert(0, file_path)
        if not dest_folder_entry.get():
            dest_folder_entry.insert(0, path.dirname(file_path))

def browse_src_folder(event=None):
    if event and event.data:
        folder_path = event.data.strip('{}')
    else:
        folder_path = filedialog.askdirectory()
    if folder_path:
        src_folder_entry.delete(0, tk.END)
        src_folder_entry.insert(0, folder_path)
        if not dest_folder_entry.get():
            dest_folder_entry.insert(0, folder_path)

def browse_dest_folder(event=None):
    if event:
        folder_path = event.data.strip('{}')
    else:
        folder_path = filedialog.askdirectory()
    if folder_path:
        dest_folder_entry.delete(0, tk.END)
        dest_folder_entry.insert(0, folder_path)

# Create GUI window
root = TkinterDnD.Tk()
root.title("AEIporter - 2024.05.10")

# Frame for conversion type selection
conversion_frame = tk.Frame(root)
conversion_frame.pack(pady=10)

folder_var = tk.BooleanVar(value=False)
tk.Checkbutton(conversion_frame, text="Convert Whole Folder", variable=folder_var).pack(side=tk.LEFT, padx=5)
overwrite_var = tk.BooleanVar()

conversion_var = tk.StringVar(root)
conversion_var.set("AEI to PNG")
tk.Radiobutton(conversion_frame, text="AEI -> PNG", variable=conversion_var, value="AEI to PNG").pack(side=tk.LEFT, padx=5)
tk.Radiobutton(conversion_frame, text="PNG -> AEI", variable=conversion_var, value="PNG to AEI").pack(side=tk.LEFT, padx=5)

# Frame for source file/folder selection
src_frame = tk.Frame(root)
src_frame.pack(pady=10)

tk.Label(src_frame, text="Source AEI File Path:").grid(row=0, column=0)
src_aei_entry = tk.Entry(src_frame, width=40)
src_aei_entry.grid(row=0, column=1)
tk.Button(src_frame, text="Browse", command=browse_src_aei_file).grid(row=0, column=2)

tk.Label(src_frame, text="Source PNG File Path:").grid(row=1, column=0)
src_png_entry = tk.Entry(src_frame, width=40)
src_png_entry.grid(row=1, column=1)
tk.Button(src_frame, text="Browse", command=browse_src_png_file).grid(row=1, column=2)

tk.Label(src_frame, text="Source Folder:").grid(row=2, column=0)
src_folder_entry = tk.Entry(src_frame, width=40)
src_folder_entry.grid(row=2, column=1)
tk.Button(src_frame, text="Browse", command=browse_src_folder).grid(row=2, column=2)

# Frame for destination folder selection
dest_frame = tk.Frame(root)
dest_frame.pack(pady=10)

tk.Label(dest_frame, text="Destination Folder:").grid(row=0, column=0)
dest_folder_entry = tk.Entry(dest_frame, width=40)
dest_folder_entry.grid(row=0, column=1)
tk.Button(dest_frame, text="Browse", command=browse_dest_folder).grid(row=0, column=2)

#Drag and drop events

src_aei_entry.drop_target_register(DND_FILES)
src_aei_entry.dnd_bind('<<Drop>>', browse_src_aei_file)

src_png_entry.drop_target_register(DND_FILES)
src_png_entry.dnd_bind('<<Drop>>', browse_src_png_file)

src_folder_entry.drop_target_register(DND_FILES)
src_folder_entry.dnd_bind('<<Drop>>', browse_src_folder)

dest_folder_entry.drop_target_register(DND_FILES)
dest_folder_entry.dnd_bind('<<Drop>>', browse_dest_folder)

# Frame for options
options_frame = tk.Frame(root)
options_frame.pack(pady=10)


tk.Checkbutton(options_frame, text="Overwrite Existing Files", variable=overwrite_var).pack(side=tk.LEFT, padx=5)
verbose_var = tk.BooleanVar()
tk.Checkbutton(options_frame, text="Verbose Output", variable=verbose_var).pack(side=tk.LEFT, padx=5)
silent_var = tk.BooleanVar()
tk.Checkbutton(options_frame, text="Silent Popups", variable=silent_var).pack(side=tk.LEFT, padx=5)

# Frame for compression format selection
compression_frame = tk.Frame(root)
compression_frame.pack(pady=10)

tk.Label(compression_frame, text="Compression Format:").pack(side=tk.LEFT, padx=5)
compression_var = tk.StringVar(root)

# Get the list of supported compression formats
supported_formats = []
for format in CompressionFormat.__members__.values():
    try:
        compressorFor(format)
        supported_formats.append(str(format).split('.')[-1])
    except UnsupportedCompressionFormatException:
        pass

# Set the default value to the first supported format
compression_var.set(supported_formats[0])

compression_menu = OptionMenu(compression_frame, compression_var, *supported_formats)
compression_menu.pack(side=tk.LEFT, padx=5)

# Convert button
tk.Button(root, text="Convert", command=convert_files).pack(pady=10)

root.mainloop()

