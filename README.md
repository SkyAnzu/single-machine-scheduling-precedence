# Single Machine Scheduling with Precedence Constraints

Dự án này dùng để so sánh nhiều encoding và solver cho bài toán lập lịch trên một máy với ràng buộc thứ tự trước-sau.

## Cấu trúc thư mục

- `common/`: các tiện ích dùng chung cho parser dataset, cấu hình đường dẫn, và kiểm tra lịch
- `Encoding/`: các triển khai solver (`seqcounter`, `seqcardenc`, `seqcardenc_ver2`, `basicsat`, `pbenc`, `gurobi`)
- `Graph_in4/`: các script tạo ảnh đồ thị precedence và xuất thống kê graph ra Excel
- `Test/`: các script runner để chạy thực nghiệm
- `Filenames/`: danh sách tên file được dùng làm nguồn xác định các instance cần chạy
- `2016/Ins/`: thư mục dataset gốc, tổ chức theo dạng `wtrd_pred{n}/{S|L}/`
- `2016/`: thư mục ghi file lời giải và tổng hợp Excel

## Cấu trúc nội bộ

Hiện tại project đã được tách thành các lớp rõ ràng hơn:

- `common/project_paths.py`: nơi tập trung các đường dẫn của project và runtime setup
- `common/dataset.py`: parser dùng chung cho các file instance `.GSP`
- `common/schedule_utils.py`: các hàm dùng chung cho window tightening, tính lateness, và validation
- `Encoding/*.py`: chỉ giữ phần modeling và solving đặc thù từng solver
- `Test/*.py`: chịu trách nhiệm điều phối thực nghiệm, resume, và ghi kết quả Excel
- `Graph_in4/*.py`: tiện ích phân tích cấu trúc precedence graph từ các file `.GSP`
- `validate_solutions.py`: công cụ CLI để validate lời giải, được xây trên các utility dùng chung

Trong `Test/` hiện có 3 runner chính:

- `run_batch_from_filelist.py`: chạy batch đầy đủ từ danh sách filename
- `run_instances_05_025_125_50_1.py`: chạy bộ benchmark cố định `XX_05_025_125_50_1.GSP`
- `run_single_instance.py`: chạy một instance lẻ, không ghi file solution hay Excel lâu dài

## Ánh xạ dataset

Batch runner hiện tại resolve file theo cách sau:

- `Filenames/10.txt` -> danh sách filename cho kích thước `10`
- `2016/Ins/wtrd_pred10/S/<filename>` -> instance kích thước `10`, loại `S`
- `2016/Ins/wtrd_pred10/L/<filename>` -> instance kích thước `10`, loại `L`

Danh sách filename là nguồn duy nhất được dùng để quyết định instance nào sẽ được chạy.

## Các solver hỗ trợ

- `seqcounter`: SAT encoding với sequential counter tự cài đặt tay
- `seqcardenc`: SAT encoding cùng ý tưởng với `seqcounter`, nhưng dùng `CardEnc`
- `seqcardenc_ver2`: biến thể của `seqcardenc` với symmetry-breaking cho các node nguồn
- `basicsat`: SAT encoding dùng cardinality encoding của PySAT
- `pbenc`: pseudo-Boolean encoding từ `pysat.pb`
- `gurobi`: mô hình MIP dùng Gurobi

Solver mặc định của batch runner là `seqcounter` và `gurobi`.

## Lệnh chạy chính

Chạy từ thư mục gốc của project:

```bash
.venv\Scripts\python Test\run_batch_from_filelist.py
.venv\Scripts\python Test\run_batch_from_filelist.py --types S
.venv\Scripts\python Test\run_batch_from_filelist.py --types L
.venv\Scripts\python Test\run_batch_from_filelist.py --types S L --solvers seqcounter seqcardenc seqcardenc_ver2 basicsat pbenc gurobi
```

Bộ benchmark đặc biệt `XX_05_025_125_50_1.GSP`:

```bash
.venv\Scripts\python Test\run_instances_05_025_125_50_1.py
.venv\Scripts\python Test\run_instances_05_025_125_50_1.py --types S L --solvers seqcardenc_ver2 gurobi
```

Chạy một instance lẻ mà không ghi output persistent:

```bash
.venv\Scripts\python Test\run_single_instance.py "2016\Ins\wtrd_pred10\S\10_05_005_100_25_1.GSP" --solver basicsat --timeout 120
.venv\Scripts\python Test\run_single_instance.py "2016\Ins\wtrd_pred10\S\10_05_005_100_25_1.GSP" --solver seqcardenc_ver2 --timeout 120
```

Sinh ảnh đồ thị precedence và xuất thống kê graph:

```bash
.venv\Scripts\python Graph_in4\visualize_gsp.py --file "2016\Ins\wtrd_pred10\S\10_05_005_100_25_1.GSP"
.venv\Scripts\python Graph_in4\visualize_gsp.py --folder "2016\Ins"
.venv\Scripts\python Graph_in4\export_stats.py
.venv\Scripts\python Graph_in4\export_stats.py --folder "2016\Ins" --out "Graph_in4\gsp_statistics.xlsx"
```

## Hành vi của batch runner

- Script: `Test/run_batch_from_filelist.py`
- Đọc filename từ `Filenames/{10|20|30|40|50}.txt`
- Resolve instance trong `2016/Ins/wtrd_pred{n}/{S|L}/`
- Ghi file lời giải vào `2016/solutions_{solver}/{n}-{type}/`
- Ghi tổng hợp Excel vào `2016/results_{solver}.xlsx`
- Tên sheet Excel có dạng `10-S`, `10-L`, `20-S`, `20-L`, ..., `50-L`
- Hỗ trợ resume bằng cách nạp lại các sheet Excel đã có và bỏ qua các filename đã hoàn thành

## Runner cho bộ benchmark đặc biệt

- Script: `Test/run_instances_05_025_125_50_1.py`
- Chạy các instance có tên cố định từ `10_05_025_125_50_1.GSP` đến `50_05_025_125_50_1.GSP`
- Hỗ trợ `seqcounter`, `seqcardenc`, `seqcardenc_ver2`, `basicsat`, `pbenc`, và `gurobi`
- Ghi file lời giải vào `2016/solutions_{solver}/{n}-{type}/`
- Ghi tổng hợp Excel vào `2016/results_{solver}_05_025_125_50_1.xlsx`
- Hỗ trợ resume từ file Excel đã tồn tại

## Runner cho một instance lẻ

- Script: `Test/run_single_instance.py`
- Nhận trực tiếp đường dẫn tới một file `.GSP`
- Hỗ trợ toàn bộ solver của batch runner
- Không ghi file solution hay Excel lâu dài vào workspace
- In ra màn hình các thông tin tóm tắt như `status`, `Lmax`, `time_s`, và `gap_%` nếu có

## Công cụ phân tích graph

- `Graph_in4/visualize_gsp.py`: đọc file `.GSP` và vẽ DAG precedence theo các layer topo
- `Graph_in4/export_stats.py`: quét một cây thư mục `.GSP` và xuất workbook Excel thống kê graph
- `Graph_in4/visualize_gsp.py` ghi ảnh vào `Graph_in4/graph/`, giữ nguyên cấu trúc thư mục tương đối của input khi chạy batch
- `Graph_in4/export_stats.py` mặc định đọc từ `2016/Ins/` và ghi file `Graph_in4/gsp_statistics.xlsx`

## Định dạng output

Mỗi solution file sẽ có dòng đầu tiên thuộc một trong các dạng sau:

- `Lmax = <value>`
- `UNSAT`
- `TIMEOUT`
- `INFEASIBLE`
- `STATUS_<code>`

Những cột Excel thường gặp:

- `solver`
- `dataset` hoặc `instance`
- `filename` hoặc `file`
- `Lmax`
- `status`
- `time_s`
- `gap_%` đối với Gurobi

## Các trạng thái thường gặp

- `FINISHED`: solver chạy xong và ghi được kết quả tóm tắt
- `UNSAT`: không tìm thấy lịch khả thi
- `TIMEOUT`: tiến trình SAT subprocess vượt quá giới hạn timeout của runner
- `TIMEOUT_NO_SOL`: Gurobi hết thời gian nhưng không tìm thấy lời giải khả thi
- `INFEASIBLE`: Gurobi chứng minh mô hình vô nghiệm
- `FILE_NOT_FOUND`: filename có trong `Filenames/` nhưng file dataset thực tế bị thiếu
- `ERROR`: lỗi runtime hoặc parsing không mong muốn

## Ghi chú

- `gurobi.lic` được đặt ở thư mục gốc của project
- `pbenc` có thể phụ thuộc vào hỗ trợ theo từng nền tảng từ các PySAT extras đã cài
- `run_gurobi.py` và `run_gurobi_10instances.py` đã được xóa vì chức năng của chúng đã được gộp vào các generic runner trong `Test/`
