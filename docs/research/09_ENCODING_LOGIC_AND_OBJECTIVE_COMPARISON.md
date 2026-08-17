# Logic Encoding Và So Sánh Objective

## 1. Mục Đích
Ghi chú này giải thích logic hiện tại của repository từ đầu đến cuối:

- các trường đầu vào và tiền xử lý
- ngữ nghĩa ràng buộc cứng dùng chung giữa các encoding
- logic tối ưu hóa incremental
- mỗi phiên bản encoding thay đổi gì so với các phiên bản khác
- objective hiện tại so sánh thế nào với Liu 2010 và Davari et al. 2016

Đây là mô tả trạng thái code của workspace hiện tại. Không phải khẳng định rằng mọi workbook lịch sử đều được sinh dưới cùng ngữ nghĩa objective.

## 2. Góc Nhìn Bài Toán Của Repository
Repository này kết hợp hai tham chiếu:

- Liu 2010 cung cấp góc nhìn objective: `1|prec, r_j|Lmax`
- Davari et al. 2016 cung cấp các trường dữ liệu dạng `.GSP` thực tế và lane benchmark mặc định dưới `2016/Ins/`

Kết quả là repository hiện tại nghiên cứu một góc nhìn hybrid:

- single machine
- ràng buộc precedence
- release dates / ready times
- due dates
- hard deadlines / time windows
- objective được hiểu là true maximum lateness

Điểm khác biệt chính: repository hiện tại dùng dữ liệu đầu vào kiểu 2016 nhưng ngữ nghĩa objective kiểu 2010.

## 3. So Sánh Objective: 2010 vs 2016 vs Code Hiện Tại

| Nguồn | Các trường / ràng buộc trong bài toán | Objective | Vai trò trong repository này |
|---|---|---|---|
| Liu 2010 | release dates, due dates, precedence, single machine | `Lmax = max_j (C_j - d_j)` | Tham chiếu objective chính |
| Davari et al. 2016 | processing time, ready date, due date, deadline, weight, precedence, time windows | `sum_j w_j T_j`, với `T_j = max(0, C_j - d_j)` | Tham chiếu định dạng dữ liệu chính |
| Repository hiện tại | trường `.GSP` kiểu 2016, precedence, hard time windows | true `Lmax = max_j (C_j - d_j)` | Luồng tối ưu hóa đang hoạt động |

Hệ quả quan trọng:

- `due date` được dùng để tính lateness trong objective.
- `deadline` được dùng làm hard window cho thời gian kết thúc.
- `weight` hiện bị bỏ qua trong luồng `Lmax` đang hoạt động.
- true `Lmax` có thể âm.
- góc nhìn bài toán hiện tại không giống với objective weighted tardiness gốc của 2016.

## 4. Định Dạng Đầu Vào Và Phân Tích
Parser của repository trong `common/dataset.py` nhận các trường `.GSP` sau:

- `n`
- `weight`
- `duration`
- `due date`
- `ready date`
- `deadline`
- `precedence relations`

Parser hiện trả về:

```text
(job_count, durations, ready_dates, due_dates, deadlines, successors)
```

Dòng `weight` được đọc để tương thích định dạng nhưng không được trả về trong tuple hiện tại và không được dùng trong luồng `Lmax` SAT.

## 5. Luồng Xử Lý Chung Của Runner
Đối với các runner thuộc họ SAT chính, luồng mặc định là:

1. Đọc instance `.GSP` bằng `common/dataset.py`.
2. Áp dụng tiền xử lý `window_tightening(...)` từ `common/schedule_utils.py`.
3. Gọi `solve_SAT(...)` của encoding với ready dates và deadlines đã được tightened.
4. Nếu khả thi, trích xuất lịch ban đầu.
5. Tính incumbent objective bằng `compute_max_lateness(..., clamp_zero=False)`.
6. Gọi `incremental_SAT_Lmax(...)` của encoding để thắt chặt incumbent dần dần.
7. Ghi file solution bằng `format_solution_text(...)`.

Ngoại lệ chính là `basicsat`, có `solve_SAT(...)` cũng nhận `due_dates` vì nó tính `Lmax` ban đầu nội bộ trước khi trả về.

## 6. Tiền Xử Lý: `window_tightening`
Đường dẫn code:

```text
common/schedule_utils.py
```

Tiền xử lý thực hiện thắt chặt bound dựa trên precedence, chỉ trên hard windows.

### 6.1. Tightened ready dates
Với mỗi job `j`, sau khi sắp xếp topo:

```text
r'_j = max(r_j, max(r'_i + p_i for i in predecessors(j)))
```

Ý nghĩa:

- một job không thể bắt đầu trước ready date của chính nó
- một job không thể bắt đầu trước khi tất cả predecessor hoàn thành

### 6.2. Tightened deadlines
Với mỗi job `i`, theo thứ tự topo ngược:

```text
D'_i = min(D_i, min(D'_j - p_j for j in successors(i)))
```

Ý nghĩa:

- một job không thể kết thúc quá muộn đến nỗi buộc successor nào đó vi phạm hard deadline của nó

### 6.3. Tiền xử lý không thay đổi gì
Tiền xử lý không sửa đổi:

- due dates
- weights
- ngữ nghĩa objective

Vậy tiền xử lý chỉ ảnh hưởng đến miền khả thi của ràng buộc cứng, không ảnh hưởng đến định nghĩa toán học của `Lmax`.

## 7. Ngữ Nghĩa Ràng Buộc Cứng Dùng Chung
Bất kể encoding nào, logic cứng đều cố gắng thực thi cùng bài toán scheduling.

### 7.1. Khả thi của time window
Với mỗi job `j`:

```text
ready_j <= start_j
start_j + p_j <= deadline_j
```

Trong hầu hết các SAT encoding, điều này xuất hiện qua việc xây dựng miền:

```text
valid_starts[j] = {ready_j, ..., deadline_j - p_j}
```

Trong `ver4_3`, biến completion-time dùng:

```text
valid_completions[j] = {ready_j + p_j, ..., deadline_j}
```

### 7.2. Capacity một máy
Tại mỗi thời điểm `t`, tối đa một job được hoạt động:

```text
sum_j A[j,t] <= 1
```

Các encoding khác nhau chỉ thay đổi cách biểu diễn ràng buộc at-most-one này.

### 7.3. Precedence
Với mỗi cung `i -> j`:

```text
start_i + p_i <= start_j
```

Một số encoding thể hiện qua start literals `S`, số khác qua order literals `L`, `G`, hoặc completion literals `C`.

### 7.4. Trích xuất lịch
Mọi encoding phải tạo ra một start time cho mỗi job, trực tiếp từ `S` hoặc gián tiếp từ order/completion variables.

## 8. Ngữ Nghĩa Objective Trong Code
Helper objective hiện tại là:

```text
compute_max_lateness(schedule, durations, due_dates, clamp_zero=False)
```

Vậy với mỗi job `j`:

```text
C_j = start_j + p_j
lateness_j = C_j - d_j
Lmax = max_j lateness_j
```

Vì `clamp_zero=False`, lịch sớm có thể cho `Lmax` âm.

## 9. Bảng Chú Giải Biến

| Họ biến | Ý nghĩa |
|---|---|
| `S[j,t]` | job `j` bắt đầu chính xác tại thời điểm `t` |
| `A[j,t]` | job `j` đang hoạt động tại thời điểm `t` |
| `L[j,t]` | job `j` bắt đầu không muộn hơn `t` |
| `G[j,t]` | job `j` bắt đầu không sớm hơn `t` |
| `C[j,t]` | job `j` kết thúc không muộn hơn `t` |

## 10. Logic Tối Ưu Hóa Incremental Dùng Chung Cho Hầu Hết SAT Encoding
Họ SAT đầu tiên tìm một lịch khả thi, sau đó cải thiện incumbent dần dần.

Nếu incumbent hiện tại là `UB`, lần gọi SAT tiếp theo tìm kiếm nghiệm tốt hơn:

```text
Lmax < UB
```

Vì thời gian là số nguyên:

```text
C_j - d_j < UB
C_j <= d_j + UB - 1
```

Với start-based encodings, điều này trở thành:

```text
start_j <= d_j + UB - p_j - 1
```

Với completion-based encodings, điều này trở thành:

```text
completion_j <= d_j + UB - 1
```

Sau mỗi model SAT:

1. trích xuất lịch
2. tính lại true `Lmax`
3. cập nhật `UB`
4. thêm clauses mạnh hơn vĩnh viễn vào cùng instance solver

Nếu solver trở thành UNSAT, incumbent trước đó là giá trị tốt nhất có thể đạt được dưới encoding hiện tại và các ràng buộc cứng.

## 11. Logic Từng Encoding Một

### 11.1. `functions_seqcounter.py`
Ý tưởng chính:

- biến start tường minh `S`
- biến activity tường minh `A`
- biến start-order tích lũy `L`
- manual sequential-counter encoding cho capacity

Logic cứng:

1. Tạo `S[j,t]` cho mọi `t` trong `valid_starts[j]`.
2. Tạo `A[j,t]` cho mọi `t` trong `[ready_j, deadline_j)`.
3. Thêm activation clauses:

```text
S[j,t0] -> A[j,t]   for t in [t0, t0 + p_j - 1]
```

4. Thêm manual sequential-counter clauses cho:

```text
sum_j A[j,t] <= 1
```

5. Xây dựng staircase variables `L[j,t]` và liên kết chúng với `S`.

Việc liên kết làm cho `L[j,t]` hoạt động như:

```text
L[j,t] = 1  iff  start_j <= t
```

Cấu trúc `L` tương tự cũng buộc chính xác một start transition cho mỗi job.

6. Thêm precedence dùng `S` và `L`:

```text
S[i,t_i] -> not L[j, t_i + p_i - 1]
```

Diễn giải:

- `L[j, t_i + p_i - 1]` nghĩa là `start_j <= t_i + p_i - 1`
- cấm nó nghĩa là `start_j >= t_i + p_i`

Logic incremental:

```text
latest_start = due_j + UB - p_j - 1
```

Sau đó:

- nếu `latest_start < min(valid_starts[j])`, thêm empty clause
- ngược lại nếu `latest_start < max(valid_starts[j])`, thêm unit clause `L[j, latest_start]`

Ý nghĩa:

```text
start_j <= due_j + UB - p_j - 1
```

### 11.2. `functions_seqcardenc.py`
Ý tưởng chính:

- cùng họ mô hình hóa với `seqcounter`: `S`, `A`, `L`
- cùng ngữ nghĩa cứng và incremental
- chỉ thay đổi capacity encoding

Khác biệt so với `seqcounter`:

- capacity dùng `PySAT CardEnc.atmost(..., encoding=EncType.seqcounter)`
- không phải sequential counter viết tay

Mọi thứ khác giữ nguyên cấu trúc:

- `S -> A`
- staircase `L`
- precedence qua `S` và `L`
- cùng rule thắt chặt incumbent

### 11.3. `functions_seqcardenc_ver2.py`
Ý tưởng chính:

- cùng lõi với `seqcardenc`
- thêm source-ready anchoring cho các job nguồn của DAG

Logic cứng bổ sung:

- tính các job lớp một với indegree `0`
- thêm một disjunctive anchor clause trên các job nguồn tại ready times của chúng

Cụ thể, clause là:

```text
S[source_1, ready_1] or S[source_2, ready_2] or ...
```

Mục đích:

- tránh symmetric drifting của tất cả job nguồn ra xa ready times của chúng
- khuyến khích ít nhất một job nguồn bắt đầu ngay tại ready date

Logic incremental:

- không đổi so với `seqcardenc`

### 11.4. `functions_seqcardenc_ver3.py`
Ý tưởng chính:

- giữ `S`, `A`, `L`
- thay đổi activity encoding để dùng order variables `L`
- giữ source-ready anchoring từ `ver2`

Khác biệt logic cứng so với `ver2`:

- cấu trúc `L` giống nhau
- capacity vẫn là `CardEnc`
- precedence vẫn dùng `S[i,t_i] -> not L[j, finish]`

Khác biệt chính là activity encoding.

Với mỗi thời điểm `t`, activity được định nghĩa qua `L` theo pattern logic:

```text
A[i,t] <-> L[i,t] and not L[i,t - p_i]
```

với xử lý edge-case gần biên trái miền.

Diễn giải:

- một job hoạt động tại thời điểm `t` nếu nó đã bắt đầu trước hoặc tại `t`
- nhưng chưa bắt đầu trước `t - p_i`

Điều này loại bỏ pattern mở rộng `S -> A` trực tiếp và thay thế bằng định nghĩa activity dựa trên order.

Logic incremental:

- không đổi, thắt chặt start-bound:

```text
L[j, due_j + UB - p_j - 1]
```

### 11.5. `functions_seqcardenc_ver4_1.py`
Ý tưởng chính:

- bỏ biến start tường minh `S`
- chỉ giữ `L` và `A`
- coi `L[j,t]` như biến start-order thuần túy

Logic cứng:

1. Tạo `L[j,t]` trực tiếp trên các valid starts.
2. Thực thi tính đơn điệu:

```text
L[j,t] -> L[j,t+1]
```

3. Buộc thời điểm cuối cùng đúng:

```text
L[j, t_max] = 1
```

Điều này có nghĩa model của mỗi job là một suffix các giá trị đúng, và `L[j,t]` đúng sớm nhất là start time được chọn.

4. Định nghĩa activity từ `L` qua helper `_append_activity_from_l(...)`, tương đương logic:

```text
A[j,t] <-> L[j,t] and not L[j, t - p_j]
```

5. Capacity vẫn là ràng buộc at-most-one trên `A`.
6. Precedence được thể hiện trực tiếp trên order variables:

```text
L[successor, s] -> L[predecessor, s - p_predecessor]
```

Diễn giải:

- nếu successor bắt đầu không muộn hơn `s`
- predecessor phải bắt đầu không muộn hơn `s - p_predecessor`

7. Source-ready anchoring chuyển thành `L[source, ready_source]`.

Logic incremental:

```text
latest_start = due_j + UB - p_j - 1
add L[j, latest_start]
```

### 11.6. `functions_seqcardenc_ver4_2.py`
Ý tưởng chính:

- giữ start-order `L`
- thêm reverse-order `G`
- tăng cường propagation qua thông tin thứ tự hai chiều

Ý nghĩa biến:

- `L[j,t]`: bắt đầu không muộn hơn `t`
- `G[j,t]`: bắt đầu không sớm hơn `t`

Logic cứng:

1. Xây dựng chuỗi đơn điệu `L` và `G`.
2. Liên kết `G[j,t]` với `not L[j,t-1]` qua clauses hai chiều.
3. Định nghĩa activity qua `L` và `G`, logic có dạng:

```text
A[j,t] <-> L[j,t] and G[j, t - p_j + 1]
```

4. Capacity vẫn là at-most-one trên `A`.
5. Precedence được thực thi theo cả hai hướng:

Dạng forward order:

```text
L[successor, s] -> L[predecessor, s - p_predecessor]
```

Dạng backward order:

```text
G[predecessor, s] -> G[successor, s + p_predecessor]
```

6. Source-ready anchoring nằm trên `L[source, ready_source]`.

Logic incremental:

- vẫn chỉ dùng start-order bound trên `L`:

```text
L[j, due_j + UB - p_j - 1]
```

`G` hỗ trợ propagation cho ràng buộc cứng, nhưng hiện không được dùng trong incumbent-bound clauses.

### 11.7. `functions_seqcardenc_ver4_3.py`
Ý tưởng chính:

- thay thế start-order variables bằng completion-order variables `C`
- căn chỉnh primary order variable với biểu thức objective thực tế

Ý nghĩa biến:

```text
C[j,t] = 1  iff  completion_j <= t
```

Logic cứng:

1. Xây dựng miền completion hợp lệ:

```text
valid_completions[j] = {ready_j + p_j, ..., deadline_j}
```

2. Thực thi tính đơn điệu:

```text
C[j,t] -> C[j,t+1]
```

3. Buộc điểm completion cuối cùng đúng.
4. Trích xuất completion được chọn là `C[j,t]` đúng sớm nhất và khôi phục:

```text
start_j = completion_j - p_j
```

5. Định nghĩa activity từ completion order, logic:

```text
A[j,t] <-> C[j, t + p_j] and not C[j,t]
```

6. Capacity vẫn là at-most-one trên `A`.
7. Precedence được viết trực tiếp trên completion variables:

```text
C[successor, c] -> C[predecessor, c - p_successor]
```

Diễn giải:

- nếu successor kết thúc không muộn hơn `c`
- thì predecessor phải kết thúc không muộn hơn thời điểm bắt đầu của successor `c - p_successor`

8. Source-ready anchoring trở thành:

```text
C[source, ready_source + p_source]
```

Logic incremental:

```text
latest_completion = due_j + UB - 1
add C[j, latest_completion]
```

Đây là biểu diễn trực tiếp và sạch nhất của strict improvement trên true `Lmax`.

### 11.8. `functions_basicsat.py`
Ý tưởng chính:

- chỉ dùng `S` và `A`
- không xây dựng staircase `L`
- encode exactly-one start tường minh bằng `CardEnc.equals`

Logic cứng:

1. Xây dựng `S[j,t]` và `A[j,t]`.
2. Thêm clauses `S -> A`.
3. Capacity qua `CardEnc.atmost`.
4. Exactly-one start mỗi job qua `CardEnc.equals`.
5. Precedence trực tiếp trên cặp start literals:

```text
if t_i + p_i > t_j:
    add not S[i,t_i] or not S[j,t_j]
```

Logic incremental:

- cấm trực tiếp từng start literal xấu:

```text
if t + p_j - due_j >= UB:
    add not S[j,t]
```

Điều này tương đương logic với các start-based encodings khác, nhưng được cài đặt không qua order variables.

### 11.9. `functions_pbenc.py`
Ý tưởng chính:

- cùng logic `S`, `A`, `L` với `seqcounter`
- capacity được encoding bằng `PBEnc.atmost`

Logic cứng:

- xây dựng miền giống hệt `seqcounter`
- `S -> A` giống hệt `seqcounter`
- staircase `L` giống hệt `seqcounter`
- precedence giống hệt `seqcounter`
- chỉ capacity encoder thay đổi từ sequential-counter clauses sang PB constraints do PySAT biên dịch

Logic incremental:

- cùng rule start-bound:

```text
L[j, due_j + UB - p_j - 1]
```

### 11.10. `functions_gurobi.py`
Ý tưởng chính:

- MIP baseline, không phải SAT encoding
- biến start integer cho mỗi job
- biến `Lmax` tường minh
- biến order nhị phân pairwise disjunctive

Biến:

- `S[j]`: integer start time
- `Lmax`: integer objective variable
- `y[i,j]`: binary pairwise order selector

Logic cứng:

1. Ràng buộc ready:

```text
S[j] >= ready_j
```

2. Ràng buộc deadline:

```text
S[j] + p_j <= deadline_j
```

3. Ràng buộc định nghĩa objective:

```text
Lmax >= S[j] + p_j - due_j
```

4. Precedence:

```text
S[i] + p_i <= S[j]
```

5. No-overlap qua big-M disjunctions:

```text
S[i] + p_i <= S[j] + M(1 - y[i,j])
S[j] + p_j <= S[i] + My[i,j]
```

Objective:

```text
minimize Lmax
```

Không giống họ SAT, baseline Gurobi không dùng vòng lặp thắt chặt incumbent của repository. MIP model tối ưu hóa `Lmax` trực tiếp bên trong solver.

## 12. Tổng Kết So Sánh Các Phiên Bản

| Phiên bản | Biến cốt lõi | Capacity encoding | Exactly-one / order mechanism | Dạng incremental bound | Điểm khác biệt chính |
|---|---|---|---|---|---|
| `seqcounter` | `S/A/L` | manual sequential counter | staircase `L` liên kết với `S` | `L[j, d_j + UB - p_j - 1]` | baseline viết tay |
| `seqcardenc` | `S/A/L` | `CardEnc.atmost` | giống `seqcounter` | giống | backend capacity sạch hơn |
| `seqcardenc_ver2` | `S/A/L` | `CardEnc.atmost` | giống `seqcardenc` | giống | source-ready anchoring |
| `seqcardenc_ver3` | `S/A/L` | `CardEnc.atmost` | cùng `L`, activity từ `L` | giống | activity encoding dựa trên order |
| `seqcardenc_ver4_1` | `L/A` | `CardEnc.atmost` | monotone `L` suffix thuần túy | cùng start bound | không có `S` tường minh |
| `seqcardenc_ver4_2` | `L/G/A` | `CardEnc.atmost` | chuỗi order hai chiều | cùng start bound | propagation mạnh hơn nhờ order |
| `seqcardenc_ver4_3` | `C/A` | `CardEnc.atmost` | monotone completion chain | `C[j, d_j + UB - 1]` | completion-order aligned với objective |
| `basicsat` | `S/A` | `CardEnc.atmost` | `CardEnc.equals` | cấm `S[j,t]` nếu xấu | dạng SAT trực tiếp đơn giản nhất |
| `pbenc` | `S/A/L` | `PBEnc.atmost` | giống `seqcounter` | cùng start bound | backend capacity PB |
| `gurobi` | `S/Lmax/y` | MIP linear constraints | tối ưu trực tiếp | không có vòng lặp SAT incremental | MIP baseline bên ngoài |

## 13. Ghi Chú Về Sự Căn Chỉnh Objective Qua Kiểm Tra Code
Tại trạng thái repository hiện tại:

- `seqcounter`, `seqcardenc`, `seqcardenc_ver2`, `seqcardenc_ver3`, `pbenc`, `basicsat`, và `gurobi` được ghi nhận trong các ghi chú protocol của repo là đã căn chỉnh về true `Lmax`.
- `ver4_1`, `ver4_2`, và `ver4_3` được viết trong code để nhắm cùng ngữ nghĩa true `Lmax`, với `ver4_3` là biểu diễn completion-order trực tiếp nhất.

Tuy nhiên:

- họ `ver4_*` đang ở giai đoạn thử nghiệm
- bất kỳ khẳng định benchmark nào liên quan đến `ver4_*` vẫn nên kiểm tra status consistency và objective consistency với một baseline đã căn chỉnh như `seqcardenc_ver3`

## 14. Cảnh Báo Quan Trọng Cho Thảo Luận Tương Lai

1. `deadline` và `due date` không thể thay thế cho nhau.

- `deadline` định nghĩa hard feasibility windows
- `due date` định nghĩa lateness trong objective

2. Bài toán trong repository hiện tại là hybrid giữa dữ liệu 2016 và suy luận objective 2010.

3. Các workbook lịch sử có thể được tạo trước khi objective được căn chỉnh.

4. Giảm số lượng clause tự nó không chứng minh được encoding tốt hơn.

5. Thảo luận Topic 1 `due + UB` cần phân biệt hai ý tưởng khác nhau:

- current incremental objective bound, đã được cài đặt dưới dạng strict
- future hard-domain tightening hoặc rebuild strategies, là các thí nghiệm mới

## 15. Tóm Tắt Thực Tế Cho Meeting
Nếu cần một bản tóm tắt ngắn:

- repository dùng dữ liệu `.GSP` định dạng 2016 nhưng tối ưu hóa true `Lmax` kiểu 2010
- tiền xử lý thắt chặt ready dates và hard deadlines dùng precedence, nhưng không thay đổi due dates hay objective
- hầu hết SAT encoding dùng chung logic thắt chặt incumbent với start bound `d_j + UB - p_j - 1`
- `ver4_3` là encoding sạch nhất vì dùng completion-order variables và incremental completion bounds `d_j + UB - 1`
- `weight` có trong dữ liệu để tương thích định dạng nhưng không được dùng trong luồng `Lmax` hiện tại

## 16. So Sánh Dataset: Liu 2010 vs Davari 2016

### 16.1 Phương pháp sinh

| Tiêu chí | Liu 2010 | Davari 2016 |
|---|---|---|
| **Nguồn** | Sinh ngẫu nhiên theo Hall & Posner (2001) | Sinh ngẫu nhiên theo Tanaka & Fujikuma + mở rộng |
| **Số instance** | 15,000 (chính) + 1,000 (randomized) | 4,320 (2 subset × 5 size × 3τ × 3ρ × 3φ × 4OS × 4 rep) |
| **Số job (n)** | 20, 40, 60, 80, 100, 200, 400, 600, 800, 1000 | 10, 20, 30, 40, 50 |
| **Processing time** | `p_j ~ U[1, 50]` | `p_j ~ U[1, α]`, α=10 (InsS) hoặc 100 (InsL) |
| **Release date** | `r_1=0`; `r_j = r_{j-1} + R_j`, `R_j ~ U[1, Rmax]` với Rmax∈{25,50,75} | `r_i ~ U[0, τ×P]` với `P=∑p_i`, τ∈{0.0, 0.5, 1.0} |
| **Due date** | `d_j = r_j + p_j + δ_j`, `δ_j ~ U[1, 50n/k]`, k∈{1,2,5,10,20} | `d_i ~ U[r_i+p_i, r_i+p_i+ρ×P]`, ρ∈{0.05, 0.25, 0.50} |
| **Deadline** | Không có (bài toán `1\|prec,r_j\|Lmax` không dùng deadline) | `δ_i ~ U[d_i, d_i+φ×P]`, φ∈{1.00, 1.25, 1.50} |
| **Weight** | Không có | `w_i ~ U[1, 10]` |
| **Precedence** | Hall-Posner: `P_ij = D(1-D)^(j-i-1)/[1-D(1-(1-D)^(j-i-1))]`, D∈{0.0,...,0.9} | RanGen software, OS∈{0.00, 0.25, 0.50, 0.75} |
| **Replications** | 10 per cell | 4 per cell |

### 16.2 Thiết kế thực nghiệm

**Liu 2010:**
- 10 (n) × 3 (Rmax) × 5 (k) × 10 (D) × 10 (rep) = **15,000 instances**
- Thêm 1,000 instances "totally randomized": `r_j, d_j ~ U[1, 25n]`
- Timeout: 60s CPU, Pentium 4 3GHz, C++
- Chỉ có type S (sparse) cho precedence — do D từ 0.0 đến 0.9, mật độ nào cũng có

**Davari 2016:**
- 2 (α∈{10,100}) × 5 (n) × 3 (τ) × 3 (ρ) × 3 (φ) × 4 (OS) × 4 (rep) = **4,320 instances**
- Timeout: 1200s, Dell Latitude i7-3720QM 2.6GHz, VC++ 2010
- Chia 2 subset riêng: InsS (p nhỏ), InsL (p lớn) — tương ứng type S và L trong repo
- Dùng RanGen để sinh precedence với OS (order strength) kiểm soát mật độ chính xác hơn Hall-Posner

### 16.3 Khác biệt chính

| Khía cạnh | Liu 2010 | Davari 2016 |
|---|---|---|
| **Deadline** | Không có. Bài toán chỉ có r_j, d_j, prec | Có deadline riêng `δ_i`. Hard time window `[r_i, δ_i]` |
| **Weight** | Không có. Objective là `Lmax`, mọi job như nhau | Có `w_i`. Dùng cho weighted tardiness |
| **Release date** | Tích lũy dần (`r_j = r_{j-1} + R_j`), tạo compatibility tự nhiên với due date | Độc lập ngẫu nhiên trong `[0, τ×P]` |
| **Due date tightness** | Phụ thuộc n: range `50n/k` tỉ lệ với số job | Phụ thuộc P: range `ρ×P` tỉ lệ với tổng processing time |
| **Mật độ precedence** | D từ 0.0 (không precedence) đến 0.9 (rất dày). Sinh bằng Hall-Posner, không đảm bảo transitive reduction | OS ∈ {0.00, 0.25, 0.50, 0.75}. Sinh bằng RanGen, có transitive reduction |
| **Kích thước instance** | Lên đến 1000 jobs | Tối đa 50 jobs |
| **Feasibility guarantee** | Không có cơ chế đặc biệt (có thể sinh instance UNSAT) | Re-index jobs theo feasible solution trước khi thêm precedence, đảm bảo luôn feasible |
| **Ý nghĩa `S`/`L`** | Không có phân loại S/L | InsS (processing time nhỏ: `U[1,10]`), InsL (processing time lớn: `U[1,100]`) |

### 16.4 Tương ứng với repo hiện tại

- **Lane `2016/Ins/`** chứa dữ liệu Davari 2016 gốc. Folder `wtrd_pred{n}/S/` = InsS, `wtrd_pred{n}/L/` = InsL
- **Tên file** `{n}_{A}_{B}_{C}_{D}_{rep}.GSP` mapping với: A~ρ (do ρ là số thập phân được mã hóa ×100), B~τ, C~φ (×100), D~OS (×100), rep ∈ {1,...,4}. Cần kiểm tra chính xác từ file gốc để xác nhận mapping.
- **Lane `Dataset_2010/`** do generator `generate_dataset_2010_pilot.py` tạo ra, mô phỏng Liu 2010 nhưng phải thêm deadline để tương thích `.GSP`, dùng công thức `deadline_i ~ U[d_i, d_i + φ×P]` kiểu Davari 2016 với φ=1.25

### 16.5 Hệ quả cho nghiên cứu

1. **Không so sánh ngang** kết quả giữa hai lane vì khác objective (`Lmax` vs `Σw_jT_j`) và khác tham số đầu vào.
2. **Deadline là điểm khác biệt quan trọng**: Liu 2010 không có deadline, nên instance có deadline chặt hơn sẽ khó hơn. Khi sinh dataset 2010, deadline được thêm vào nhân tạo — đây là yếu tố cần ghi nhận khi đánh giá độ khó.
3. **Compatibility**: Liu 2010 sinh release date tích lũy → r và d có compatibility tự nhiên. Davari 2016 sinh r và d độc lập → có thể tạo instance khó hơn do time window không aligned.
4. **Feasibility**: Instance Davari 2016 có cơ chế đảm bảo feasible (re-index + RanGen). Instance Liu 2010 (và 2010-generated) có thể UNSAT — cần kiểm tra khi benchmark.
5. **Scale**: Liu 2010 có instance đến 1000 jobs (dùng B&B). Davari 2016 chỉ đến 50 jobs (dùng MIP/SAT), phù hợp với quy mô thử nghiệm SAT encoding của repo.

### 16.6 Trạng thái thực tế của lane `Dataset_2010` hiện tại

Lane `Dataset_2010/` được sinh bởi `Test/generate_dataset_2010_pilot.py` với cấu hình **pilot**, không phải full grid như Liu 2010 gốc:

| Tham số | Liu 2010 gốc | Dataset_2010 pilot hiện tại |
|---|---|---|
| n | 20,40,60,80,100,200,400,600,800,1000 | **20, 40, 50** |
| Release date (Rmax) | 25, 50, 75 | **25, 50** |
| Due divisor (k) | 1, 2, 5, 10, 20 | **5, 10** |
| Precedence density (D) | 0.0, 0.1, ..., 0.9 | **0.2, 0.6** |
| Deadline phi | Không có (thêm `phi=1.25` để tương thích `.GSP`) | **1.25** (cố định) |
| Replications | 10 | **1** (pilot) |
| Tổng instance | 15,000 | **24** (3 size × 2 Rmax × 2 k × 2 D × 1 rep) |

**Điểm khác biệt so với Liu 2010 gốc:**
- Dataset gốc không có deadline; pilot phải thêm `deadline_i ~ U[d_i, d_i + phi*P]` (phi=1.25) để tương thích parser `.GSP` — mượn công thức từ Davari 2016
- Chỉ sinh type `S` (không có `L`), vì không có phân biệt InsS/InsL
- Tên file dạng `20_liu_r25_k05_d20_phi125_1.GSP` thay vì format Davari
- Precedence dùng Hall-Posner (như Liu 2010), không dùng RanGen

**Hỗ trợ full profile:** generator có flag `--profile full` sẽ mở rộng về grid Liu 2010 gốc (n đến 1000, D từ 0.0 đến 0.9, k từ 1 đến 20, Rmax thêm 75, 10 replications), nhưng chưa chạy. Lane hiện tại chỉ là pilot/demo như đã ghi trong `docs/research/02_DATASET_POLICY.md`.
