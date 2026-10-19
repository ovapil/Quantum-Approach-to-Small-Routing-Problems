
# ⚛️ Quantum Approach to Small Routing Problems

> **Đồ án thuộc khuôn khổ môn học Điện toán lượng tử (Quantum Computing) – Trường Đại học Công nghệ Thông tin (UIT), ĐHQG-HCM.**

**Quantum Approach to Small Routing Problems** (Phương pháp lượng tử giải quyết các bài toán định tuyến quy mô nhỏ) là đồ án nghiên cứu ứng dụng phương pháp tối ưu lượng tử vào bài toán tìm đường đi ngắn nhất trong mạng máy tính.

Đồ án tập trung xây dựng các topology mạng quy mô nhỏ từ **6–10 node**, mô hình hóa bài toán **Shortest Path** dưới dạng **Quadratic Unconstrained Binary Optimization (QUBO)**, sử dụng **Quantum Approximate Optimization Algorithm (QAOA)** trên bộ mô phỏng lượng tử và so sánh kết quả với thuật toán **Dijkstra** truyền thống.

---

## 👥 Thành viên thực hiện

| STT | Họ và tên | MSSV | Email |
|:---:|---|:---:|---|
| 1 | **[Lê Nhật Trinh Nguyên]** | [23521040] | [23521040@gm.uit.edu.vn] |
| 2 | **[Huỳnh Thị Phương Nghi]** | [23521001] | [23521001@gm.uit.edu.vn] |

---

## 🎯 Mục tiêu đồ án

- Xây dựng các topology mạng nhỏ gồm **6–10 node**, với trọng số biểu diễn độ trễ hoặc chi phí truyền dẫn.
- Mô hình hóa bài toán tìm đường đi ngắn nhất dưới dạng **QUBO** với các ràng buộc bảo toàn luồng.
- Sử dụng **QAOA** trên bộ mô phỏng lượng tử để tìm nghiệm và giải mã thành đường đi thực tế.
- Cài đặt thuật toán **Dijkstra** làm phương pháp đối chứng cổ điển.
- So sánh chất lượng nghiệm và phân tích sự gia tăng số qubit khi kích thước topology thay đổi.

---

## 📖 Problem Definition

Bài toán đặt ra là tìm đường đi có tổng chi phí nhỏ nhất giữa một node nguồn (**source**) và một node đích (**destination**) trong mạng có trọng số.

Mạng được biểu diễn bằng đồ thị:

**G = (V, E)**

Trong đó:

- **G (Graph):** Đồ thị biểu diễn topology mạng.
- **V (Vertices):** Tập hợp các node trong mạng.
- **E (Edges):** Tập hợp các liên kết giữa các node.
- **w (Weight):** Trọng số của mỗi liên kết, biểu diễn độ trễ hoặc chi phí truyền dẫn.
- **s (Source):** Node nguồn.
- **t (Destination):** Node đích.

Mục tiêu là xác định một đường đi hợp lệ từ **s** đến **t** sao cho tổng trọng số của các liên kết trên đường đi là nhỏ nhất.

---


## 📚 Graph Representation

Trong đồ án, topology mạng được biểu diễn dưới dạng
**đồ thị có trọng số (Weighted Graph)**:

\[
G = (V, E)
\]

Trong đó:

- **Graph (Đồ thị):** Mô hình biểu diễn cấu trúc
  kết nối giữa các thiết bị trong mạng.
- **Vertex/Node (Đỉnh):** Đại diện cho một thiết bị
  mạng, chẳng hạn như router hoặc switch.
- **Edge/Link (Cạnh):** Đại diện cho kết nối giữa
  hai node trong mạng.
- **Path (Đường đi):** Chuỗi các node liên tiếp
  được kết nối bởi các edge.
- **Cycle (Chu trình):** Đường đi khép kín bắt đầu
  và kết thúc tại cùng một node, không lặp các
  node trung gian.
- **Weight (Trọng số):** Giá trị gắn với mỗi edge,
  đại diện cho độ trễ hoặc chi phí truyền dẫn.

### Shortest Path Problem

**Shortest Path Problem** là bài toán tìm đường đi
có tổng trọng số nhỏ nhất giữa một node nguồn
(**Source**) và một node đích (**Destination**).

Chi phí của một đường đi được tính bằng tổng
trọng số của tất cả các edge thuộc đường đi đó.


## 🔀 Đồ thị có hướng và đồ thị vô hướng

### 1. Đồ thị vô hướng (Undirected Graph)

**Đồ thị vô hướng** là loại đồ thị mà các cạnh không có hướng xác định. Nếu hai node A và B được kết nối với nhau, ta có thể di chuyển theo cả hai chiều:

- **A → B:** Di chuyển từ node A đến node B.
- **B → A:** Di chuyển từ node B đến node A.

Trong đồ thị vô hướng có trọng số, chi phí của một liên kết là như nhau ở cả hai chiều.

**Ví dụ:** Nếu liên kết giữa A và B có trọng số bằng 5 thì:

- Chi phí từ A đến B là 5.
- Chi phí từ B đến A cũng là 5.

Trong thư viện **NetworkX**, đồ thị vô hướng được biểu diễn bằng `nx.Graph()`.

### 2. Đồ thị có hướng (Directed Graph)

**Đồ thị có hướng** là loại đồ thị mà mỗi cạnh có một hướng xác định, quy định chiều di chuyển giữa các node.

Ví dụ, nếu tồn tại cạnh **A → B** thì:

- Có thể di chuyển từ node A đến node B.
- Không thể mặc định di chuyển từ node B về node A nếu không tồn tại cạnh **B → A**.

Đối với đồ thị có hướng có trọng số, hai cạnh ngược chiều có thể mang trọng số khác nhau.

**Ví dụ:**

- **A → B:** Trọng số bằng 3.
- **B → A:** Trọng số bằng 7.

Trong thư viện **NetworkX**, đồ thị có hướng được biểu diễn bằng `nx.DiGraph()`.

### 3. So sánh hai loại đồ thị

| Tiêu chí | Đồ thị vô hướng | Đồ thị có hướng |
|---|---|---|
| **Hướng liên kết** | Không có hướng xác định | Có hướng xác định |
| **Di chuyển giữa hai node** | Có thể đi theo cả hai chiều | Phụ thuộc vào hướng của cạnh |
| **Trọng số hai chiều** | Giống nhau | Có thể khác nhau |
| **Biểu diễn trong NetworkX** | `nx.Graph()` | `nx.DiGraph()` |

### 4. Lựa chọn loại đồ thị cho đồ án

Trong giai đoạn đầu, nhóm đề xuất sử dụng **đồ thị vô hướng có trọng số (Undirected Weighted Graph)** để biểu diễn topology mạng.

Lý do lựa chọn:

- **Đơn giản hóa mô hình:** Các liên kết được biểu diễn dưới dạng hai chiều với cùng một trọng số.
- **Thuận tiện kiểm chứng:** Dễ dàng tính toán thủ công và đối chiếu kết quả tìm đường đi ngắn nhất.
- **Hỗ trợ Dijkstra:** Phù hợp để xây dựng phương pháp đối chứng cổ điển.
- **Chuẩn bị cho QUBO:** Giúp nhóm bắt đầu với cấu trúc mạng đơn giản trước khi xây dựng mô hình tối ưu lượng tử.

Việc lựa chọn loại đồ thị sẽ được nhóm thống nhất trước khi triển khai chính thức.

### 5. Node nguồn, node đích và chi phí liên kết

Trong bài toán tìm đường đi ngắn nhất, cần xác định ba thành phần quan trọng:

- **Node nguồn (Source - s):** Node bắt đầu của đường đi.
- **Node đích (Destination - t):** Node cần đến.
- **Chi phí liên kết (Link Cost - w):** Trọng số gắn với mỗi liên kết, biểu diễn độ trễ hoặc chi phí truyền dẫn.

## 🌐 Topology thử nghiệm Tuần 1

### 1. Thiết kế topology

Nhóm đề xuất xây dựng một **đồ thị vô hướng có trọng số**
(Undirected Weighted Graph) gồm **6 node và 7 liên kết**
để thử nghiệm bài toán tìm đường đi ngắn nhất.

Đồ thị được biểu diễn bởi:

**G = (V, E)**

Trong đó:

- **V = {A, B, C, D, E, F}:** Tập hợp các node.
- **E:** Tập hợp các liên kết giữa các node.
- **Weight:** Trọng số giả định biểu diễn chi phí truyền dẫn.

### 2. Danh sách liên kết và trọng số

| STT | Liên kết | Trọng số |
|:---:|:---:|:---:|
| 1 | A - B | 4 |
| 2 | A - C | 2 |
| 3 | B - D | 5 |
| 4 | C - D | 3 |
| 5 | C - E | 6 |
| 6 | D - F | 2 |
| 7 | E - F | 1 |

### 3. Xác định node nguồn và node đích

- **Node nguồn (Source):** A
- **Node đích (Destination):** F

Mục tiêu là tìm đường đi từ node A đến node F
có tổng trọng số nhỏ nhất.

### 4. Tính toán thủ công các đường đi

Các đường đi đơn hợp lệ từ A đến F gồm:

| Route | Đường đi | Tổng chi phí |
|:---:|---|:---:|
| P1 | A → B → D → F | 4 + 5 + 2 = 11 |
| P2 | A → B → D → C → E → F | 4 + 5 + 3 + 6 + 1 = 19 |
| P3 | A → C → D → F | 2 + 3 + 2 = 7 |
| P4 | A → C → E → F | 2 + 6 + 1 = 9 |

### 5. Kết quả kỳ vọng

Qua việc so sánh tổng chi phí của các đường đi,
ta xác định được:

- **Shortest Path:** A → C → D → F
- **Minimum Path Cost:** 7
- **Number of Nodes:** 6
- **Number of Edges:** 7

Đường đi **A → C → D → F** có tổng trọng số
nhỏ nhất trong các đường đi hợp lệ được xét.

Kết quả tính toán thủ công này sẽ được sử dụng
làm cơ sở kiểm chứng thuật toán Dijkstra
trong các bước tiếp theo.

### 6. Ghi chú

Topology hiện tại là mô hình thử nghiệm ban đầu.
Các trọng số là dữ liệu giả định và có thể được
điều chỉnh sau khi nhóm thống nhất cấu hình.

Việc sử dụng đồ thị vô hướng có trọng số
cần được xác nhận trước khi triển khai QUBO.


## 🧮 Thuật toán Dijkstra (Classical Baseline)

### 1. Giới thiệu

**Dijkstra** là thuật toán tìm đường đi ngắn nhất từ
một node nguồn đến các node khác trong đồ thị có
trọng số không âm.

Trong đồ án, thuật toán Dijkstra được sử dụng làm
**phương pháp đối chứng cổ điển (Classical Baseline)**
để đánh giá kết quả tìm đường bằng QAOA.

### 2. Nguyên lý hoạt động

Thuật toán Dijkstra thực hiện các bước:

1. **Khởi tạo:** Gán khoảng cách từ node nguồn đến
   chính nó bằng 0 và đến các node khác bằng vô cực.

2. **Lựa chọn node:** Chọn node chưa được xử lý
   có khoảng cách tạm thời nhỏ nhất.

3. **Cập nhật khoảng cách:** Kiểm tra các node kề
   và cập nhật nếu tìm được đường đi có chi phí thấp hơn.

4. **Đánh dấu:** Đánh dấu node vừa chọn là đã xử lý.

5. **Lặp lại:** Tiếp tục cho đến khi node đích
   được xử lý hoặc không còn node có thể đến được.

Thao tác cập nhật khoảng cách được gọi là
**Relaxation**, có công thức:

$$
d(v) = \min(d(v), d(u) + w(u,v))
$$

Trong đó:

- **d(u):** Khoảng cách ngắn nhất hiện biết đến node u.
- **d(v):** Khoảng cách ngắn nhất hiện biết đến node v.
- **w(u,v):** Trọng số của liên kết giữa u và v.
### 3. Vai trò của Dijkstra trong đồ án

Dijkstra được sử dụng để:

- Xác định đường đi ngắn nhất với chi phí tối ưu.
- Làm cơ sở kiểm chứng các nghiệm tìm được bằng QAOA.
- So sánh tổng chi phí giữa phương pháp cổ điển
  và phương pháp lượng tử.
- Đánh giá chất lượng nghiệm và tỷ lệ tìm được
  đường đi tối ưu của QAOA.

Dijkstra đảm bảo tìm được đường đi ngắn nhất
trong đồ thị có trọng số không âm, trong khi
QAOA không đảm bảo luôn thu được nghiệm tối ưu.


## 🌐 Week 1 Test Topology

*Nội dung sẽ được bổ sung trong Tuần 1.*
