import tkinter as tk
from tkinter import messagebox
import pickle

class QuantumChipGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Quantum Chip Coupling Map")
        self.canvas = tk.Canvas(root, width=800, height=1000, bg="white")
        self.canvas.pack()

        self.nodes = {}  # 存储节点位置，编号: (x, y)
        self.edges = []  # 存储连线 (node1, node2)
        self.selected_nodes = []  # 临时存储被选择的节点
        self.node_radius = 10
        self.file_name = "coupling_map.pkl"  # 使用 pickle 保存的文件

        # 每次启动时清空文件
        # with open(self.file_name, 'wb') as f:
        #     pickle.dump(self.edges, f)

        self.create_nodes()

    def create_nodes(self):
        spacing_x = 100  # 横向间距
        spacing_y = 60   # 纵向间距
        offset_x = 50    # 水平偏移量
        offset_y = 50    # 垂直偏移量

        count = 0
        for row in range(11):  # 13 行
            for col in range(6):
                # 反转偏移：偶数行保持不变，奇数行增加右移
                x = offset_x + col * spacing_x + (1 - row % 2) * (spacing_x // 2)
                y = offset_y + row * spacing_y
                node_id = f"{count:02d}"
                self.nodes[node_id] = (x, y)
                self.draw_node(x, y, node_id)
                count += 1
                if count > 65:
                    break


    def draw_node(self, x, y, node_id):
        # 绘制节点圆
        node = self.canvas.create_oval(x - self.node_radius, y - self.node_radius,
                                       x + self.node_radius, y + self.node_radius,
                                       fill="lightblue", outline="black", tags="node")
        # 绘制编号
        text = self.canvas.create_text(x, y, text=node_id, tags="node")

        # 绑定点击事件到这个节点的圆形和文本
        self.canvas.tag_bind(node, "<Button-1>", lambda event, node_id=node_id: self.select_node(node_id))
        self.canvas.tag_bind(text, "<Button-1>", lambda event, node_id=node_id: self.select_node(node_id))

    def select_node(self, node_id):
        if node_id not in self.selected_nodes:
            self.selected_nodes.append(node_id)
            print(f"Selected node: {node_id}")
            if len(self.selected_nodes) == 2:
                self.create_edge(self.selected_nodes[0], self.selected_nodes[1])
                self.selected_nodes = []  # 清空已选节点

    def create_edge(self, node1, node2):
        x1, y1 = self.nodes[node1]
        x2, y2 = self.nodes[node2]
        self.canvas.create_line(x1, y1, x2, y2, fill="black", width=2)
        self.edges.append([node1, node2])
        print(f"Edge created: {node1} - {node2}")

        # 实时保存列表到 pickle 文件
        with open(self.file_name, 'wb') as f:
            pickle.dump(self.edges, f)

    def finish(self):
        # 输出所有的连线
        print("Final coupling map: ", self.edges)
        messagebox.showinfo("Result", f"Coupling map: {self.edges}")

if __name__ == "__main__":
    root = tk.Tk()
    gui = QuantumChipGUI(root)

    finish_button = tk.Button(root, text="Finish", command=gui.finish)
    finish_button.pack()

    root.mainloop()
