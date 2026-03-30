# Single Machine Scheduling with Precedence Constraints

Dự án này phục vụ thực nghiệm cho bài toán lập lịch trên một máy với ràng buộc precedence, trọng tâm là so sánh nhiều SAT encoding và một mô hình MIP dùng Gurobi.

Nếu cần context kỹ thuật sâu hơn để sửa code, đọc thêm `AIREADME.md`. `README.md` đóng vai trò bản mô tả đầy đủ cho workspace, còn `AIREADME.md` là bản implementation context cho các session kỹ thuật.

## Tổng quan workspace

Thư mục gốc hiện tại gồm các phần chính sau:

- `Encoding/`: các solver và encoding chính
- `Test/`: các runner để chạy thực nghiệm
- `common/`: utility dùng chung cho parser dataset, path, validation, và schedule helpers
- `Graph_in4/`: utility phân tích DAG precedence, vẽ graph, và xuất thống kê Excel
- `Filenames/`: danh sách tên file instance theo từng kích thước `10, 20, 30, 40, 50`
- `2016/Ins/`: bộ dữ liệu chính đang dùng trong runner
- `2016/`: nơi ghi lời giải và file Excel kết quả thực nghiệm
- `2013/`: bộ dữ liệu cũ, hiện không được các runner chính sử dụng
- `validate_solutions.py`: CLI để kiểm tra một file lời giải với một instance
- `requirements.txt`: dependency Python
- `gurobi.lic`: license Gurobi đặt ở thư mục gốc project

## Cấu trúc thư mục chi tiết

- `common/project_paths.py`: khai báo `PROJECT_ROOT`, `INS_DIR`, `OUTPUT_DIR`, danh sách solver, và runtime setup
- `common/dataset.py`: parser dùng chung cho file `.GSP`
- `common/schedule_utils.py`: `window_tightening`, `compute_max_lateness`, `compute_job_lateness`, `format_solution_text`, `validate_schedule`
- `Encoding/functions_seqcounter.py`: bản sequential-counter tự cài đặt tay
- `Encoding/functions_seqcardenc.py`: bản giống `seqcounter` nhưng phần cardinality dùng `CardEnc`
- `Encoding/functions_seqcardenc_ver2.py`: bản `seqcardenc` cộng thêm symmetry-breaking cho các node nguồn của DAG
- `Encoding/functions_basicsat.py`: SAT encoding dùng cardinality encoding của PySAT
- `Encoding/functions_pbenc.py`: pseudo-Boolean encoding dùng `pysat.pb`
- `Encoding/functions_gurobi.py`: mô hình MIP với Gurobi
- `Test/runner_common.py`: tầng dùng chung cho toàn bộ runner thực nghiệm
- `Test/run_batch_from_filelist.py`: runner batch theo danh sách file trong `Filenames/`
- `Test/run_instances_05_025_125_50_1.py`: runner cho bộ benchmark đặc biệt `XX_05_025_125_50_1.GSP`
- `Test/run_single_instance.py`: chạy một instance lẻ, không ghi output persistent ra workspace
- `Test/rewrite_existing_solutions.py`: script migrate/rewrite toàn bộ `solution.txt` đã có sang format mới
- `Graph_in4/visualize_gsp.py`: vẽ DAG precedence của file `.GSP`
- `Graph_in4/visualize_batch_from_filelist.py`: batch visualizer chỉ xử lý các instance được liệt kê trong `Filenames/`
- `Graph_in4/export_stats.py`: thống kê graph của cả thư mục `.GSP` ra Excel

## Dữ liệu và ánh xạ đường dẫn

Runner hiện tại dùng bộ dữ liệu `2016/Ins/` với ánh xạ như sau:

- `Filenames/10.txt` -> danh sách filename cho kích thước `10`
- `Filenames/20.txt` -> danh sách filename cho kích thước `20`
- `...`
- `2016/Ins/wtrd_pred10/S/<filename>` -> instance loại `S`, kích thước `10`
- `2016/Ins/wtrd_pred10/L/<filename>` -> instance loại `L`, kích thước `10`
- tương tự cho `20`, `30`, `40`, `50`

Danh sách filename trong `Filenames/` là nguồn duy nhất để quyết định batch runner và batch visualizer sẽ quét những instance nào.

## Bộ dữ liệu nào đang được dùng

- `2016/Ins/`: bộ dữ liệu chính dùng trong toàn bộ runner hiện tại
- `2013/`: chỉ còn được giữ trong workspace, chưa được nối vào runner hiện tại
- `2016/Q1/`: đã được loại khỏi Git bằng `.gitignore`

## Các solver hiện có

- `seqcounter`: SAT encoding với sequential counter tự viết tay
- `seqcardenc`: cùng logic với `seqcounter`, nhưng cardinality constraint dùng `CardEnc`
- `seqcardenc_ver2`: thêm symmetry-breaking trên tập node nguồn của đồ thị precedence
- `basicsat`: SAT encoding dùng cardinality encoding của PySAT
- `pbenc`: pseudo-Boolean encoding dùng `pysat.pb`
- `gurobi`: mô hình MIP dùng Gurobi

Danh sách solver chung hiện được khai báo ở `common/project_paths.py`.

## Các điểm giống nhau giữa các SAT solver

Các runner hiện tại đều xử lý preprocess trước khi vào solver:

- đọc instance từ `.GSP`
- gọi `window_tightening(...)`
- truyền `new_ready_dates` và `new_deadlines` vào solver

Điều này có nghĩa là các file encoding như `seqcounter`, `seqcardenc`, `seqcardenc_ver2`, `pbenc` không tự gọi `window_tightening` bên trong `solve_SAT(...)`; preprocessing được thực hiện ở `Test/runner_common.py`.

## Validation hiện nằm ở đâu

Logic validation chính hiện nằm ở:

- `common/schedule_utils.py`

Nó kiểm tra 5 nhóm ràng buộc:

- `C1`: mọi job đều được schedule
- `C2`: start/end nằm trong cửa sổ hợp lệ theo ready date và deadline
- `C3`: không có overlap trên máy đơn
- `C4`: số lượng job trong schedule đúng bằng `n`
- `C5`: precedence được tôn trọng

`validate_solutions.py` bây giờ chủ yếu là CLI wrapper để validate thủ công một cặp `instance + solution file`.

## Runner hiện có

### 1. Batch runner chung

File: `Test/run_batch_from_filelist.py`

Chức năng:

- đọc danh sách filename từ `Filenames/{10,20,30,40,50}.txt`
- resolve instance trong `2016/Ins/wtrd_pred{n}/{S|L}/`
- chạy từng solver trên từng instance
- ghi file lời giải vào `2016/solutions_{solver}/{n}-{type}/`
- ghi tổng hợp vào `2016/results_{solver}.xlsx`
- hỗ trợ resume từ file Excel đã có

Các solver hỗ trợ:

- `seqcounter`
- `seqcardenc`
- `seqcardenc_ver2`
- `basicsat`
- `pbenc`
- `gurobi`

### 2. Runner cho bộ benchmark đặc biệt

File: `Test/run_instances_05_025_125_50_1.py`

Chức năng:

- chỉ chạy các file có dạng `10_05_025_125_50_1.GSP` đến `50_05_025_125_50_1.GSP`
- hỗ trợ cùng tập solver như batch runner
- ghi tổng hợp vào `2016/results_{solver}_05_025_125_50_1.xlsx`

### 3. Runner cho một instance lẻ

File: `Test/run_single_instance.py`

Chức năng:

- nhận trực tiếp path tới một file `.GSP`
- chạy đúng một solver trên đúng một instance
- không ghi file solution hay Excel lâu dài vào workspace
- dùng file tạm để lấy kết quả rồi tự xóa
- in ra `status`, `Lmax`, `time`, và `gap` nếu có

## Timeout hiện được định nghĩa thế nào

Đây là điểm quan trọng cho thực nghiệm:

- timeout thực nghiệm chuẩn là `300s` cho mỗi instance
- nếu một run vượt `300s`, kết quả được ghi nhận là `TIMEOUT`
- thời gian báo cáo khi timeout được cố định là `300.00s`
- runner vẫn cho tiến trình con thêm `20s` ngầm để tự ghi file và thoát sạch, nhưng khoảng này không được tính vào `time_s`

Nói ngắn gọn:

- `300s` là hard timeout về mặt báo cáo và phân tích thực nghiệm
- `20s` chỉ là grace nội bộ để subprocess cleanup

Chỗ triển khai nằm ở:

- `Test/run_batch_from_filelist.py`
- `Test/run_instances_05_025_125_50_1.py`
- `Test/runner_common.py`

## Công cụ phân tích graph

### `Graph_in4/visualize_gsp.py`

Chức năng:

- đọc file `.GSP`
- dựng DAG precedence
- sắp node theo topological layers
- hiển thị thêm `ready date`, `due date`, `deadline` bên cạnh từng node
- chỉ vẽ precedence giữa `n` job thật, không tính dummy node `n+1`
- xuất ảnh `.png`

Đầu ra mặc định:

- `Graph_in4/graph/`

Khi chạy ở chế độ folder, script sẽ giữ nguyên cấu trúc thư mục tương đối của input bên dưới `graph/`.

Khi chạy ở chế độ single-file, script hiện cũng tự suy ra mốc `Ins/` nếu có, nên output vẫn giữ được nhánh `wtrd_predXX/S|L/...` thay vì dồn tất cả ảnh vào cùng một thư mục.

### `Graph_in4/visualize_batch_from_filelist.py`

Chức năng:

- đọc danh sách filename từ `Filenames/{10,20,30,40,50}.txt`
- resolve instance trong `2016/Ins/wtrd_pred{n}/{S|L}/`
- chỉ vẽ đúng các instance có trong danh sách
- ghi ảnh vào `Graph_in4/graph_batch/`

Output hiện tại có dạng:

- `Graph_in4/graph_batch/wtrd_pred10/S/<filename>.png`

### `Graph_in4/export_stats.py`

Chức năng:

- quét toàn bộ `.GSP` dưới một thư mục gốc
- thống kê số job, số cạnh, số layer, và min/max của weight, duration, ready date, due date, deadline
- ghi workbook Excel nhiều sheet

Đường dẫn mặc định hiện tại:

- input mặc định: `2016/Ins/`
- output mặc định: `Graph_in4/gsp_statistics.xlsx`

## Các lệnh chạy thường dùng

## Môi trường và dependency

Project hiện đang được chạy qua `.venv` ở thư mục gốc.

Các gói trong `requirements.txt` đủ cho runner và Excel output chính, nhưng nhóm utility trong `Graph_in4/` còn cần thêm:

- `networkx`
- `matplotlib`

Nếu chưa có, có thể cài thêm bằng:

```bash
.venv\Scripts\pip install networkx matplotlib
```

Sau khi cài, hai script `Graph_in4/visualize_gsp.py` và `Graph_in4/export_stats.py` mới chạy đầy đủ.

### Batch runner

```bash
.venv\Scripts\python Test\run_batch_from_filelist.py
.venv\Scripts\python Test\run_batch_from_filelist.py --types S
.venv\Scripts\python Test\run_batch_from_filelist.py --types L
.venv\Scripts\python Test\run_batch_from_filelist.py --types S L --solvers seqcounter seqcardenc seqcardenc_ver2 basicsat pbenc gurobi
```

### Runner cho bộ benchmark đặc biệt

```bash
.venv\Scripts\python Test\run_instances_05_025_125_50_1.py
.venv\Scripts\python Test\run_instances_05_025_125_50_1.py --types S L --solvers seqcardenc_ver2 gurobi
```

### Chạy một instance lẻ

```bash
.venv\Scripts\python Test\run_single_instance.py "2016\Ins\wtrd_pred10\S\10_05_005_100_25_1.GSP" --solver basicsat --timeout 120
.venv\Scripts\python Test\run_single_instance.py "2016\Ins\wtrd_pred10\S\10_05_005_100_25_1.GSP" --solver seqcardenc_ver2 --timeout 120
```

### Vẽ graph và xuất thống kê graph

```bash
.venv\Scripts\python Graph_in4\visualize_gsp.py --file "2016\Ins\wtrd_pred10\S\10_05_005_100_25_1.GSP"
.venv\Scripts\python Graph_in4\visualize_gsp.py --folder "2016\Ins"
.venv\Scripts\python Graph_in4\visualize_batch_from_filelist.py
.venv\Scripts\python Graph_in4\visualize_batch_from_filelist.py --types S
.venv\Scripts\python Graph_in4\visualize_batch_from_filelist.py --sizes 10 20 --types S L --workers 4
.venv\Scripts\python Graph_in4\export_stats.py
.venv\Scripts\python Graph_in4\export_stats.py --folder "2016\Ins" --out "Graph_in4\gsp_statistics.xlsx"
```

### Rewrite lại solution cũ theo format mới

```bash
.venv\Scripts\python Test\rewrite_existing_solutions.py
.venv\Scripts\python Test\rewrite_existing_solutions.py --solver gurobi --limit 5
.venv\Scripts\python Test\rewrite_existing_solutions.py --write
```

### Validate một lời giải

```bash
.venv\Scripts\python validate_solutions.py "2016\Ins\wtrd_pred10\S\10_05_005_100_25_1.GSP" "2016\solutions_seqcounter\10-S\10_05_005_100_25_1.GSP.txt"
```

## Định dạng output của solver

Một file lời giải hiện thường bắt đầu bằng một trong các dòng sau:

- `Lmax = <value> (Job <id>)`
- `Lmax = <value> (Jobs <id1>, <id2>, ...)`
- `UNSAT`
- `TIMEOUT`
- `INFEASIBLE`
- `STATUS_<code>`

Với file có lịch hợp lệ, từng dòng job hiện có dạng:

- `Job i: start = s, end = e, due_date = d, lateness = e - d`

Format này được dùng thống nhất cho runner mới và cũng có thể được áp dụng lại cho lời giải cũ bằng `Test/rewrite_existing_solutions.py`.

Các cột thường gặp trong Excel kết quả:

- `solver`
- `dataset` hoặc `instance`
- `filename` hoặc `file`
- `Lmax`
- `status`
- `time_s`
- `gap_%` đối với Gurobi

## Ý nghĩa status

- `FINISHED`: solver chạy xong và có kết quả tóm tắt hợp lệ
- `UNSAT`: không tìm thấy lịch khả thi
- `TIMEOUT`: vượt quá hard timeout `300s`
- `INFEASIBLE`: Gurobi chứng minh mô hình vô nghiệm
- `FILE_NOT_FOUND`: filename có trong danh sách nhưng file thực tế không tồn tại
- `ERROR`: lỗi runtime hoặc parse không mong muốn

Lưu ý: các status cũ như `TIMEOUT_NO_SOL` hiện không còn là trạng thái chính trong luồng runner đã sửa timeout.

## Git và file bị loại khỏi repo

`.gitignore` hiện loại các mục đáng chú ý sau:

- `.venv/`
- `2013/`
- `2016/Q1/`
- `gurobi.lic`
- `*.pdf`
- `__pycache__/`, `*.pyc`
- `nul`

Nếu thấy xuất hiện file `nul` ở root workspace, đó thường là artefact do dùng redirect kiểu `cmd` trong PowerShell, ví dụ `> nul`. Trong PowerShell nên dùng `> $null` hoặc `| Out-Null`.

## Điều cần nhớ khi quay lại project

- dataset thực nghiệm chính là `2016/Ins/`
- mọi runner chính đều đi qua `Test/runner_common.py`
- preprocessing `window_tightening` được gọi ở runner, không phải bên trong từng solver SAT
- `seqcardenc_ver2` hiện đã được tích hợp vào toàn bộ runner như các solver khác
- hard timeout thực nghiệm là `300s`
- `Graph_in4/` là nhánh tiện ích riêng để quan sát và thống kê đồ thị precedence
- `README.md` này được xem như bản mô tả chuẩn của workspace hiện tại
