import os
import csv
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
import mplcursors
import parser

##########################################################################
# 마우스 이벤트 인덱스 (Line, Offset)
g_start_idx = None
g_end_idx   = None
repeat_line = [0, 0]
pattern_offset = [[0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]]
pattern_num = len(pattern_offset)

# 데이터
read_log = ""
open_file_name = ""
parser_data = None

# 아이콘
icon_size = 20        # 크기
border_thickness = 2  # 테두리 두께

# 그래프 사이즈
INIT_GRAPH_SIZE = (10, 5)

# 색상
BLACK  = "#000000"
YELLOW = "#FFFFE0"
RED    = "#FFCCCB"
BLUE   = "#ADD8E6"
GREEN  = "#CCFFCC"
GRAY   = "#F0F0F0"
DARK_RED = "#8B0000"
line_colors = [RED, GREEN, BLUE]
##########################################################################

def on_closing():
    root.quit()

def get_line_num(text_widget_index):
    return int(text_widget_index.split('.')[0])

def get_offset_num(text_widget_index):
    return  int(text_widget_index.split('.')[1])

def on_drag(event):
    try:
        start = text_widget.index(tk.SEL_FIRST)
        end = text_widget.index(tk.SEL_LAST)
        text_widget.tag_add("drag_highlight", start, end)
        text_widget.tag_configure("drag_highlight", foreground=DARK_RED)
    except tk.TclError:
        pass

def on_double_click(event):
    click_index = text_widget.index(f"@{event.x},{event.y}")
    # TODO
    print("[bind-event] double :", click_index)

def on_left_button_down(event):
    global g_start_idx
    g_start_idx = text_widget.index(f"@{event.x},{event.y}")
    print("[bind-event] down   :", g_start_idx)
    text_widget.tag_remove("drag_highlight", "1.0", tk.END)

def on_left_button_up(event):
    global g_end_idx
    g_end_idx = text_widget.index(f"@{event.x},{event.y}")
    print("[bind-event] up     :", g_end_idx)

def set_log_repeat_pattern():
    global g_start_idx, g_end_idx
    start = min(get_line_num(g_start_idx), get_line_num(g_end_idx))
    end   = max(get_line_num(g_start_idx), get_line_num(g_end_idx))
    if start and end:
        text_widget.tag_remove("repeat_line", "1.0", tk.END)
        for idx in range(pattern_num):
            text_widget.tag_remove("pattern_{}".format(idx), "1.0", tk.END)
        for line in range(start, end + 1):
            start_index = f"{line}.0"
            end_index = f"{line}.end + 1c"
            text_widget.tag_add("repeat_line", start_index, end_index)
            text_widget.tag_config("repeat_line", background=YELLOW)
        repeat_line[0] = start
        repeat_line[1] = end
        print("[set_repeat_line] start / end : {} / {}".format(repeat_line[0], repeat_line[1]))

def set_pattern(idx, color):
    global read_log, repeat_line, pattern_offset, g_start_idx, g_end_idx
    if repeat_line == [0, 0]:
        messagebox.showerror("Error", "Please set the repeat lines.")
        return
    if get_line_num(g_start_idx) != get_line_num(g_end_idx):
        messagebox.showerror("Error", "The selected pattern contains newline.")
        return
    if not (repeat_line[0] <= get_line_num(g_start_idx) and get_line_num(g_start_idx) <= repeat_line[1]):
        messagebox.showerror("Error", "Select a pattern within 'repeat lines'.")
        return
    start = min(get_offset_num(g_start_idx), get_offset_num(g_end_idx))
    end   = max(get_offset_num(g_start_idx), get_offset_num(g_end_idx))
    select_line = read_log.splitlines()[get_line_num(g_start_idx)-1]
    select_pattern = select_line[start:end]
    if " " in select_pattern:
        print("{}".format(select_pattern.replace(" ", "_")))
        messagebox.showerror("Error", "The selected pattern contains spaces.")
        return
    pattern_offset[idx][0] = get_line_num(g_start_idx)
    pattern_offset[idx][1] = start
    pattern_offset[idx][2] = get_line_num(g_end_idx)
    pattern_offset[idx][3] = end
    text_widget.tag_remove("pattern_{}".format(idx), "1.0", tk.END)
    text_widget.tag_add("pattern_{}".format(idx), g_start_idx, g_end_idx)
    text_widget.tag_config("pattern_{}".format(idx), background=color, foreground=BLACK)
    print("[set_pattern_#{}] data : '{}' / offset : {}".format(idx+1, select_pattern, pattern_offset[idx]))

def on_right_click(event):
    popup_menu = tk.Menu(root, tearoff=0)
    popup_menu.add_command(label="Set Log Repeat Pattern", command=set_log_repeat_pattern, image=yellow_icon, compound=tk.LEFT)
    popup_menu.add_separator()
    data_pattern_menu = tk.Menu(popup_menu, tearoff=0)
    data_pattern_menu.add_command(label="Pattern #1", command=lambda: set_pattern(0, RED), image=red_icon, compound=tk.LEFT)
    data_pattern_menu.add_command(label="Pattern #2", command=lambda: set_pattern(1, GREEN), image=green_icon, compound=tk.LEFT)
    data_pattern_menu.add_command(label="Pattern #3", command=lambda: set_pattern(2, BLUE), image=blue_icon, compound=tk.LEFT)
    popup_menu.add_cascade(label="Set Data Pattern", menu=data_pattern_menu)
    popup_menu.add_separator()
    popup_menu.add_command(label="Generate Graph", command=generate_graph, compound=tk.LEFT)
    popup_menu.post(event.x_root, event.y_root)

def initialize_graph():
    fig, ax = plt.subplots(figsize=(INIT_GRAPH_SIZE))
    ax.plot([])
    ax.set_title("Empty Chart")
    canvas = FigureCanvasTkAgg(fig, master=graph_frame)
    canvas.draw()
    canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

def generate_graph():
    global read_log, repeat_line, pattern_offset, parser_data, open_file_name
    if read_log == "":
        messagebox.showerror("Error", "Please select a file.")
        return
    if repeat_line == [0, 0]:
        messagebox.showerror("Error", "Please set the repeat lines.")
        return
    if pattern_offset == [[0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]]:
        messagebox.showerror("Error", "Please set the pattern.")
        return
    parser_data = parser.parser_main(read_log, repeat_line, pattern_offset)
    print(parser_data)

    filtered_data = []
    for entry in parser_data:
        filtered_data.append([value for value in entry if value is not None])

    x = range(len(filtered_data))                      # x축 값 (인덱스 값으로 설정)
    fig, ax = plt.subplots(figsize=(INIT_GRAPH_SIZE))  # 그래프 크기 (가로, 세로)

    lines = []
    for i in range(len(max(filtered_data, key=len))):
        y = [entry[i] if i < len(entry) else None for entry in filtered_data]
        line, = ax.plot(x, y, marker='o', linestyle='-', label=f'Pattern #{i+1}', color=line_colors[i % len(line_colors)])
        lines.append(line)

    ax.set_title(open_file_name)
    ax.legend()

    cursor = mplcursors.cursor(lines, hover=True)  # 마우스 이벤트 (툴팁) 추가
    cursor.connect("add", lambda sel: sel.annotation.set_text(f"({int(sel.target[0])}, {sel.target[1]:.2f})"))

    for widget in graph_frame.winfo_children():
        widget.destroy()
    canvas = FigureCanvasTkAgg(fig, master=graph_frame)
    canvas.draw()
    canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

def init_data():
    global read_log, repeat_line, pattern_offset
    read_log = ""
    repeat_line = [0, 0]
    pattern_offset = [[0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]]

def open_file():
    global read_log, open_file_name
    file_path = filedialog.askopenfilename(title="Open File", filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")])
    if not file_path:
        return
    init_data()
    open_file_name = os.path.basename(file_path)
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            file = open(file_path, "r")
            content = file.read()
            read_log = content
            text_widget.delete(1.0, tk.END)
            text_widget.insert(tk.END, content)
    except FileNotFoundError:
        print("File not found. Please check the file path.")

def export_csv():
    global parser_data
    if parser_data == None:
        messagebox.showerror("Error", f"Failed to export the CSV file. Please try again after generating graph.")
        return
    file_path = filedialog.asksaveasfilename(title="Export as CSV", defaultextension=".csv", filetypes=[("CSV Files", "*.csv"), ("All Files", "*.*")])
    if not file_path:
        return
    with open(file_path, mode="w", newline="") as file:
        writer = csv.writer(file)
        writer.writerows(parser_data)

def create_icon(color):
    icon = tk.PhotoImage(width=icon_size, height=icon_size)
    for x in range(border_thickness, icon_size - border_thickness):
        for y in range(border_thickness, icon_size - border_thickness):
            icon.put(color, (x, y))        # 배경
    for x in range(icon_size):
        icon.put(BLACK, (x, 0))            # 윗 테두리
        icon.put(BLACK, (x, icon_size-1))  # 아랫 테두리
        icon.put(BLACK, (0, x))            # 왼쪽 테두리
        icon.put(BLACK, (icon_size-1, x))  # 오른쪽 테두리
    return icon

if __name__ == "__main__":
    root = tk.Tk()
    root.title("log2graph")
    root.geometry("1200x500")
    root.resizable(False, False)
    root.protocol("WM_DELETE_WINDOW", on_closing)

    # 메인 프레임
    main_frame = ttk.Frame(root)
    main_frame.pack(fill=tk.BOTH, expand=True)

    # 텍스트 프레임
    text_button_frame = ttk.Frame(main_frame, height=50)
    text_button_frame.grid(row=0, column=0)
    text_frame = ttk.Frame(main_frame, width=400)
    text_frame.grid(row=1, column=0, sticky="nsew")

    # 그래프 프레임
    graph_frame = ttk.Frame(main_frame, width=800, relief=tk.SUNKEN, borderwidth=1)
    graph_frame.grid(row=0, column=1, rowspan=2, sticky="nsew", padx=5)

    # Grid 레이아웃 설정
    main_frame.grid_rowconfigure(1, weight=1)  # 텍스트 프레임의 가로/세로 확장
    main_frame.grid_columnconfigure(1, weight=1)  # 그래프 프레임의 확장 허용

    # 그래프 프레임 구성
    initialize_graph()

    # 텍스트 프레임 구성
    open_button = ttk.Button(text_button_frame, text="Open File", command=open_file)
    open_button.grid(row=0, column=0)
    export_button = ttk.Button(text_button_frame, text="Export CSV", command=export_csv)
    export_button.grid(row=0, column=1)
    vertical_scroll = tk.Scrollbar(text_frame, orient=tk.VERTICAL)
    vertical_scroll.pack(side=tk.RIGHT, fill=tk.Y)
    horizontal_scroll = tk.Scrollbar(text_frame, orient=tk.HORIZONTAL)
    horizontal_scroll.pack(side=tk.BOTTOM, fill=tk.X)
    text_widget = tk.Text(text_frame, wrap=tk.NONE, yscrollcommand=vertical_scroll.set, xscrollcommand=horizontal_scroll.set, bg=GRAY, state="normal")
    text_widget.pack(fill=tk.BOTH, expand=True)
    vertical_scroll.config(command=text_widget.yview)
    horizontal_scroll.config(command=text_widget.xview)

    # 아이콘 색상 정의
    red_icon    = create_icon(RED)
    green_icon  = create_icon(GREEN)
    blue_icon   = create_icon(BLUE)
    yellow_icon = create_icon(YELLOW)

    # 이벤트 바인딩
    text_widget.bind("<B1-Motion>", on_drag)
    text_widget.bind("<Double-1>", on_double_click)
    text_widget.bind("<ButtonPress-1>", on_left_button_down)
    text_widget.bind("<ButtonRelease-1>", on_left_button_up)
    text_widget.bind("<Button-3>", on_right_click)

    text_widget.delete(1.0, tk.END)
    text_widget.insert(tk.END, "Please open the file")

    root.mainloop()