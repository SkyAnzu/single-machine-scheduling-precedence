# Single-Machine Scheduling with Precedence and Time Windows

Dự án này phục vụ nghiên cứu nội bộ về SAT encoding cho bài toán lập lịch trên một máy với ràng buộc precedence và time-window-style data.

Repo hiện kết hợp hai mạch tham chiếu:
- Liu 2010: bài toán `1|prec, r_j|Lmax`, tức tối thiểu hóa maximum lateness.
- Davari et al. 2016: bộ dữ liệu / định dạng `.GSP` có `release date`, `due date`, `deadline`, `weight`, precedence, ban đầu gắn với objective weighted tardiness.

Trong workspace này, lane dữ liệu mặc định đi theo cấu trúc của bộ 2016, còn phần so sánh encoding SAT đang được đặt trong bối cảnh nghiên cứu mục tiêu `Lmax` kiểu 2010.

## Những điều quan trọng cần biết ngay

- `2016/Ins/` là lane benchmark chính hiện tại.
- `Dataset_2010/` hiện chỉ là lane sinh thử / demo, không phải benchmark chính thức.
- `Filenames/{size}-{type}.txt` nếu có, fallback `Filenames/{size}.txt`, và `Dataset_2010/Filenames/*.txt` là nguồn authoritative cho batch runner.
- Trường `weight` có trong file `.GSP`, nhưng current `Lmax` workflow không sử dụng nó trong objective.
- Objective semantics hiện tại đã align về true `Lmax = max(C_j - d_j)` cho `seqcounter`, `seqcardenc`, `seqcardenc_ver2`, `seqcardenc_ver3`, `pbenc`, `basicsat`, và `gurobi`.
- Không trộn workbook lịch sử với kết quả mới nếu chưa ghi rõ code state, vì workbook cũ có thể được tạo trước khi objective được align.

## Repo này đang nghiên cứu gì?

Câu hỏi nghiên cứu chính hiện tại là:
- các encoding SAT trong họ `seqcardenc*` khác nhau thế nào về khả năng giải, runtime, và hành vi solver;
- khi dùng cùng dataset lane, cùng preprocessing và cùng timeout, biến thể nào ổn hơn trên các instance khó;
- lane dữ liệu mặc định là dữ liệu 2016, nhưng góc nhìn objective và benchmark reasoning lại bám theo bài 2010 về `Lmax`.

Nói ngắn gọn:
- paper 2016 cho repo này "hình dạng dữ liệu" và lane benchmark mặc định;
- paper 2010 cho repo này "góc nhìn objective" và cảm hứng sinh dữ liệu exploratory.

## Hai bài tham khảo gốc

### Liu 2010
File local:
- `2010 (Q1) - Single machine scheduling to minimize maximum lateness subject to release dates and precedence constraints.pdf`

Ý chính:
- bài toán `1|prec, r_j|Lmax`
- mục tiêu là true maximum lateness `Lmax = max_j (C_j - d_j)`
- `Lmax` có thể âm nếu mọi job hoàn thành sớm
- tác giả dùng branch-and-bound, lower bound từ relaxed preemptive problem
- bộ test sinh hệ thống, phần lớn instance được giải trong 1 phút CPU

### Davari et al. 2016
File local:
- `2016 (Q1) - Exact algorithms for single-machine scheduling with time windows and precedence constraints.pdf`

Ý chính:
- mỗi job có `processing time`, `release date`, `due date`, `deadline`, `weight`
- có precedence constraints và time window `[r_j, delta_j]`
- objective gốc của paper là tổng weighted tardiness, không phải `Lmax`
- repo hiện dùng kiểu dữ liệu này làm đầu vào `.GSP`

## Cấu trúc workspace

### 1. `Encoding/`
Chứa các solver / encoding đang được so sánh.

Các file chính:
- `functions_seqcounter.py`: sequential counter tự cài đặt tay, có biến staircase `L`
- `functions_seqcardenc.py`: logic gần `seqcounter`, nhưng capacity dùng `PySAT CardEnc`
- `functions_seqcardenc_ver2.py`: thêm source-ready anchoring constraint cho các source job của DAG precedence
- `functions_seqcardenc_ver3.py`: biến thể từ `ver2`, thay phần kích hoạt activity bằng encode dựa trên quan hệ giữa `A` và `L`
- `functions_basicsat.py`: SAT encoding gọn hơn, dùng `S/A` và exact-one start bằng `CardEnc`
- `functions_pbenc.py`: capacity bằng `pysat.pb`
- `functions_gurobi.py`: MIP baseline với Gurobi

### 2. `Test/`
Chứa runner để chạy thực nghiệm.

Các file chính:
- `runner_common.py`: tầng dùng chung cho runner, parse output, ghi Excel, gọi preprocessing
- `run_batch_from_filelist.py`: runner batch cho lane `2016/Ins/`
- `run_instances_05_025_125_50_1.py`: runner cho family đặc biệt `XX_05_025_125_50_1.GSP`
- `run_single_instance.py`: chạy một instance lẻ, không ghi output persistent
- `run_batch_dataset_2010.py`: runner cho lane generated demo `Dataset_2010/`
- `generate_dataset_2010_pilot.py`: sinh dữ liệu demo / pilot cho `Dataset_2010/`

### 3. `common/`
Chứa thành phần dùng chung.

- `project_paths.py`: root paths, dataset paths, solver list, runtime environment
- `dataset.py`: parser `.GSP`; có đọc phần `weight` nhưng tuple trả về hiện không mang `weight`
- `schedule_utils.py`: `window_tightening`, tính lateness, format solution, validate schedule

### 4. `Filenames/`
Chứa danh sách tên instance cho lane chính `2016`.

- `10.txt`, `20.txt`, `30.txt`, `40.txt`, `50.txt`
- type-specific filelist như `10-L.txt` được ưu tiên khi tồn tại
- batch runner và batch visualizer đều dùng rule: `Filenames/{size}-{type}.txt` trước, fallback `Filenames/{size}.txt`

### 5. `Graph_in4/`
Công cụ quan sát DAG precedence và thống kê dataset.

- `visualize_gsp.py`: vẽ một file `.GSP` hoặc cả folder
- `visualize_batch_from_filelist.py`: chỉ vẽ những instance có trong `Filenames/`
- `export_stats.py`: xuất thống kê graph sang Excel
- output mặc định:
  - `Graph_in4/graph/`
  - `Graph_in4/graph_batch/`
  - `Graph_in4/gsp_statistics.xlsx`

### 6. `2016/`
Chứa lane benchmark chính và output thực nghiệm mặc định.

- `2016/Ins/`: input lane chính
- `2016/results_*.xlsx`: workbook kết quả
- `2016/solutions_{solver}/...`: solution text theo solver

### 7. `Dataset_2010/`
Lane generated để demo / pilot.

- `Dataset_2010/Ins/`: instance `.GSP` được sinh ra
- `Dataset_2010/Filenames/`: filelist cho batch runner của lane này
- `Dataset_2010/results_*.xlsx`: kết quả lane demo
- `Dataset_2010/solutions_{solver}/...`: solution text lane demo

### 8. `docs/research/`
Protocol và template nghiên cứu.

- `01_PROTOCOL_SCOPE.md`
- `02_DATASET_POLICY.md`
- `03_EXPERIMENT_RUNBOOK.md`
- `04_METRICS_GUIDE.md`
- `05_REPORT_TEMPLATE.md`
- `06_DECISION_LOG.md`

### 9. File khác
- `validate_solutions.py`: validate một cặp `instance + solution`
- `requirements.txt`: dependency Python
- `gurobi.lic`: local license file cho Gurobi nếu có, không version-control
- PDF 2010/2016: tài liệu tham khảo đọc tại chỗ

## Lane dữ liệu và mapping path

### Lane A mặc định: `2016/Ins/`
Mapping chính:
- `Filenames/10-S.txt` nếu tồn tại, nếu không fallback `Filenames/10.txt` -> `2016/Ins/wtrd_pred10/S/<filename>`
- `Filenames/10-L.txt` nếu tồn tại, nếu không fallback `Filenames/10.txt` -> `2016/Ins/wtrd_pred10/L/<filename>`
- `Filenames/20.txt` -> `2016/Ins/wtrd_pred20/{S|L}/<filename>`
- `Filenames/30.txt` -> `2016/Ins/wtrd_pred30/{S|L}/<filename>`
- `Filenames/40.txt` -> `2016/Ins/wtrd_pred40/{S|L}/<filename>`
- `Filenames/50.txt` -> `2016/Ins/wtrd_pred50/{S|L}/<filename>`

Các batch runner mặc định không quét toàn bộ folder `Ins/`; chúng đọc filelist trước rồi mới resolve path.

### Lane B generated demo: `Dataset_2010/`
Mapping chính:
- `Dataset_2010/Filenames/20.txt` -> `Dataset_2010/Ins/wtrd_pred20/S/<filename>`
- `Dataset_2010/Filenames/40.txt` -> `Dataset_2010/Ins/wtrd_pred40/S/<filename>`
- `Dataset_2010/Filenames/50.txt` -> `Dataset_2010/Ins/wtrd_pred50/S/<filename>`

Lane này hiện được dùng để sinh thử và quan sát, chưa nên gộp vào benchmark summary mặc định.

### Caveat hiện tại của `Dataset_2010/`
Workspace hiện có thể chứa nhiều file `.GSP` hơn số file đang được liệt kê trong `Dataset_2010/Filenames/*.txt`.

Điều đó có nghĩa là:
- runner sẽ chỉ chạy những gì có trong filelist;
- không được suy luận quy mô benchmark chỉ bằng cách đếm file trong folder `Ins/`;
- nếu muốn mở rộng lane demo, cần cập nhật filelist hoặc ghi rõ đang dùng folder scan thay vì filelist.

## Solver inventory và current objective behavior

| Solver | Vai trò chính | Objective behavior hiện tại |
|---|---|---|
| `seqcounter` | SAT, sequential counter thủ công | true `Lmax = max(C_j - d_j)` |
| `seqcardenc` | SAT, capacity bằng `CardEnc` | true `Lmax` |
| `seqcardenc_ver2` | `seqcardenc` + source-ready anchoring | true `Lmax` |
| `seqcardenc_ver3` | `ver2` + encode activity khác | true `Lmax` |
| `basicsat` | SAT đơn giản hơn, exact-one start | true `Lmax` |
| `pbenc` | SAT / PB hybrid cho capacity | true `Lmax` |
| `gurobi` | MIP baseline | true `Lmax` |

Hệ quả:
- so sánh status và feasibility vẫn có ý nghĩa ở nhiều tình huống;
- so sánh objective số học giữa solver hiện tại chỉ nên thực hiện sau khi xác nhận workbook được tạo dưới code state đã align objective.

## Preprocessing và validation

### Preprocessing
Tất cả runner chính đều đi qua:
- đọc instance `.GSP`
- gọi `window_tightening(...)`
- truyền `new_ready_dates` và `new_deadlines` vào solver

Điểm này nằm ở:
- `Test/runner_common.py`

Do đó:
- không nên giả định mỗi file trong `Encoding/` tự làm preprocessing giống nhau;
- fairness của benchmark phải giữ nguyên runner / preprocessing.

### Validation
Validation hard constraints dùng:
- `common/schedule_utils.py`
- `validate_solutions.py` chỉ là CLI wrapper

Các nhóm constraint đang kiểm:
- mọi job được schedule
- start / end hợp lệ theo window
- không overlap trên single machine
- số lượng job đúng bằng `n`
- precedence được tôn trọng

## Runner và output

### 1. Batch runner chính
File:
- `Test/run_batch_from_filelist.py`

Chức năng:
- chạy theo rule `Filenames/{size}-{type}.txt` trước, fallback `Filenames/{size}.txt`
- lane input mặc định là `2016/Ins/`
- output:
  - `2016/solutions_{solver}/{n}-{type}/`
  - `2016/results_{solver}.xlsx`

Timeout:
- `300s` / instance

Lưu ý:
- khi không truyền `--solvers`, runner dùng default từ `common/project_paths.py`
- default hiện tại là `seqcounter` và `gurobi`
- với benchmark nghiên cứu, nên luôn truyền `--solvers` tường minh
- `time_s` trong workbook là wall time của subprocess runner, không phải pure solver-search time
- batch vẫn giữ solution chi tiết (`start`, `end`, `due_date`, `lateness`) để phục vụ kiểm tra sau khi chạy
- batch solution persistent không kèm `SAT stats`

### 2. Runner family đặc biệt
File:
- `Test/run_instances_05_025_125_50_1.py`

Chức năng:
- chỉ chạy các file dạng `XX_05_025_125_50_1.GSP`
- output:
  - `2016/results_{solver}_05_025_125_50_1.xlsx`

Timeout:
- `300s` / instance

### 3. Runner một instance lẻ
File:
- `Test/run_single_instance.py`

Chức năng:
- chạy một `.GSP` duy nhất
- không ghi workbook hay solution persistent
- dùng file tạm rồi tự xóa
- in ra `status`, `Lmax`, `time`, `gap` và SAT stats nếu solver cung cấp được
- SAT stats là thông tin diagnostic cho single-instance, không phải artifact mặc định của batch run

### 4. Runner lane demo `Dataset_2010`
File:
- `Test/run_batch_dataset_2010.py`

Chức năng:
- chạy theo `Dataset_2010/Filenames/*.txt`
- output:
  - `Dataset_2010/solutions_{solver}/{n}-{type}/`
  - `Dataset_2010/results_{solver}.xlsx`

Timeout:
- mặc định `60s` / instance
- có thể override bằng `--timeout`
- `time_s` trong workbook vẫn là wall time của subprocess runner

### 5. Generator lane demo
File:
- `Test/generate_dataset_2010_pilot.py`

Chức năng:
- sinh dữ liệu `.GSP` để test nhanh ý tưởng
- default:
  - size `20, 40, 50`
  - một grid nhỏ để demo
- hỗ trợ `--profile pilot` và `--profile full`

Nhưng trong context repo hiện tại:
- đây là generator demo / pilot;
- không nên coi output hiện tại là benchmark canonical nếu chưa freeze filelist và policy sinh dữ liệu.

## Định dạng output của solution file

Một file solution thường bắt đầu bằng một trong các dòng:
- `Lmax = <value>`
- `UNSAT`
- `TIMEOUT`
- `TIME_LIMIT_FEASIBLE`
- `INFEASIBLE`
- `STATUS_<code>`

Với schedule hợp lệ, mỗi dòng job thường có dạng:
- `Job i: start = s, end = e, due_date = d, lateness = e - d`

Trong single-instance diagnostic, một số SAT solver có thể cung cấp thêm:
- `conflicts`
- `decisions`
- `propagations`
- `restarts`

Batch solution persistent hiện không ghi `SAT stats`.

## Status semantics

- `FINISHED`: runner đọc được output hợp lệ
- `UNSAT`: solver không tìm thấy lịch khả thi
- `TIMEOUT`: vượt hard timeout của runner
- `TIME_LIMIT_FEASIBLE`: Gurobi chạm time limit, có incumbent, nhưng MIP gap vẫn khác 0; workbook ghi `Lmax = -` và `gap_%` giữ gap
- `INFEASIBLE`: Gurobi chứng minh vô nghiệm
- `FILE_NOT_FOUND`: tên có trong filelist nhưng file input không tồn tại
- `ERROR`: lỗi parse hoặc lỗi runtime

Lưu ý:
- `FINISHED` ở đây có nghĩa là runner parse được output kết thúc hợp lệ
- validation hard constraints vẫn là bước riêng nếu cần audit solution sâu hơn

## Công cụ graph

### `Graph_in4/visualize_gsp.py`
- `--file <path>`: vẽ một instance
- `--folder <path>`: quét đệ quy cả folder
- `--workers N`: số worker cho mode folder
- output mặc định: `Graph_in4/graph/`

### `Graph_in4/visualize_batch_from_filelist.py`
- chỉ xử lý instance nằm trong filelist theo rule `Filenames/{size}-{type}.txt` trước, fallback `Filenames/{size}.txt`
- output mặc định: `Graph_in4/graph_batch/`

### `Graph_in4/export_stats.py`
- quét một folder `.GSP`
- xuất workbook thống kê
- mặc định:
  - input: `2016/Ins/`
  - output: `Graph_in4/gsp_statistics.xlsx`

## Môi trường chạy

Repo hiện giả định:
- Python environment trong `.venv/`
- dependency trong `requirements.txt`

Các gói đáng chú ý:
- `python-sat`
- `pandas`
- `openpyxl`
- `gurobipy`
- `networkx`
- `matplotlib`

Khác với một số ghi chú cũ, `networkx` và `matplotlib` đã có sẵn trong `requirements.txt`.

## Lệnh thường dùng

### Batch benchmark trên lane 2016
```bash
.venv\Scripts\python Test\run_batch_from_filelist.py --types S L --solvers seqcardenc seqcardenc_ver2 seqcardenc_ver3
.venv\Scripts\python Test\run_batch_from_filelist.py --types S L --solvers seqcounter seqcardenc seqcardenc_ver2 seqcardenc_ver3 basicsat pbenc gurobi
```

### Chạy family đặc biệt
```bash
.venv\Scripts\python Test\run_instances_05_025_125_50_1.py --types S L --solvers seqcardenc_ver2 seqcardenc_ver3 gurobi
```

### Chạy một instance lẻ
```bash
.venv\Scripts\python Test\run_single_instance.py "2016\Ins\wtrd_pred10\S\10_05_005_100_25_1.GSP" --solver basicsat --timeout 120
.venv\Scripts\python Test\run_single_instance.py "2016\Ins\wtrd_pred10\S\10_05_005_100_25_1.GSP" --solver seqcardenc_ver2 --timeout 120
```

### Sinh và chạy lane demo `Dataset_2010`
```bash
.venv\Scripts\python Test\generate_dataset_2010_pilot.py
.venv\Scripts\python Test\run_batch_dataset_2010.py --types S --solvers seqcardenc_ver2 --sizes 20 40 50 --timeout 60
```

### Vẽ graph và xuất thống kê
```bash
.venv\Scripts\python Graph_in4\visualize_gsp.py --file "2016\Ins\wtrd_pred10\S\10_05_005_100_25_1.GSP"
.venv\Scripts\python Graph_in4\visualize_gsp.py --folder "2016\Ins" --workers 4
.venv\Scripts\python Graph_in4\visualize_batch_from_filelist.py --sizes 10 20 --types S L --workers 4
.venv\Scripts\python Graph_in4\export_stats.py --folder "2016\Ins" --out "Graph_in4\gsp_statistics.xlsx"
```

### Validate một lời giải
```bash
.venv\Scripts\python validate_solutions.py "2016\Ins\wtrd_pred10\S\10_05_005_100_25_1.GSP" "2016\solutions_seqcounter\10-S\10_05_005_100_25_1.GSP.txt"
```

## Khi đọc kết quả, đừng giả định sai

- `2016` trong repo hiện tại không có nghĩa là repo đang giải đúng nguyên objective của paper 2016.
- Có `weight` trong input không đồng nghĩa là solver đang tối ưu weighted tardiness.
- Có chữ `Lmax` trong output không đồng nghĩa workbook đó được tạo dưới code state objective-aligned hiện tại.
- Có nhiều file trong một folder không đồng nghĩa batch runner sẽ chạy hết; filelist mới là nguồn quyết định.

## Tài liệu protocol nên đọc tiếp

- `AGENTS.md`
- `docs/research/01_PROTOCOL_SCOPE.md`
- `docs/research/02_DATASET_POLICY.md`
- `docs/research/03_EXPERIMENT_RUNBOOK.md`
- `docs/research/04_METRICS_GUIDE.md`
- `docs/research/05_REPORT_TEMPLATE.md`
- `docs/research/06_DECISION_LOG.md`

## Tóm tắt một câu

Repo này là workspace nghiên cứu so sánh SAT encoding cho single-machine scheduling with precedence / time windows, dùng lane dữ liệu kiểu 2016 làm mặc định, nhưng đang được phân tích chủ yếu dưới góc nhìn objective true `Lmax` kiểu 2010.
