import csv


def save_text(filename, datas):
    with open(filename, "w", encoding="utf-8") as f:
        for line in datas:
            f.write(str(line) + "\n")


def read_file(filename, skip_first_line=False):
    datas = []
    with open(filename, "r", encoding="utf-8") as f:
        if skip_first_line: next(f)
        for line in f:
            datas.append(line.strip())
    return datas


def save_csv(filename, datas):
    with open(filename, "w", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        for line in datas:
            writer.writerow(line)


def read_csv(filename, skip_first_line=False):
    with open(filename, "r", encoding="utf-8-sig") as f:
        reader = csv.reader(x.replace("\0", "") for x in f)
        datas = [row for row in reader]
        if skip_first_line:
            datas = datas[1:]
    return datas


def reader_csv(filename, skip_first_line=False):
    with open(filename, "r", encoding="utf-8") as f:
        if skip_first_line:
            next(f)
        reader = csv.reader(x.replace("\0", "") for x in f)
        return reader