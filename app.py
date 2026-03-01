from flask import Flask, render_template, request, send_file, redirect, url_for
import pandas as pd
import os

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'

if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])


# ---------------------------------
# Snake Distribution Algorithm
# ---------------------------------
def create_balanced_groups(df, num_groups):
    df = df.sort_values(by="Grade in pre", ascending=False).reset_index(drop=True)
    groups = [[] for _ in range(num_groups)]

    direction = 1
    group_index = 0

    for _, row in df.iterrows():
        groups[group_index].append(row.to_dict())

        if direction == 1:
            group_index += 1
            if group_index == num_groups:
                group_index -= 1
                direction = -1
        else:
            group_index -= 1
            if group_index < 0:
                group_index += 1
                direction = 1

    return groups


# ---------------------------------
# Calculate Stats
# ---------------------------------
def calculate_stats(group):
    df = pd.DataFrame(group)
    avg_marks = round(df["Grade in pre"].mean(), 2)
    male_count = len(df[df["Gender"] == "Male"])
    female_count = len(df[df["Gender"] == "Female"])
    return avg_marks, male_count, female_count


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        file = request.files["file"]
        num_groups = int(request.form["groups"])

        if not file:
            return redirect(url_for("index"))

        filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(filepath)

        if file.filename.endswith(".csv"):
            df = pd.read_csv(filepath)
        else:
            df = pd.read_excel(filepath)

        groups = create_balanced_groups(df, num_groups)

        group_data = []
        all_students = []
        group_averages = []

        for i, group in enumerate(groups):
            avg, male, female = calculate_stats(group)
            group_averages.append(avg)

            group_data.append({
                "students": group,
                "avg": avg,
                "male": male,
                "female": female
            })

            for student in group:
                student_copy = student.copy()
                student_copy["Group"] = f"Group {i+1}"
                all_students.append(student_copy)

        # GAP CALCULATION
        highest_avg = max(group_averages)
        lowest_avg = min(group_averages)
        gap = round(highest_avg - lowest_avg, 2)

        overall_avg = round(df["Grade in pre"].mean(), 2)

        # Save Excel
        output_file = os.path.join(app.config['UPLOAD_FOLDER'], "group_output.xlsx")
        pd.DataFrame(all_students).to_excel(output_file, index=False)

        return render_template(
            "result.html",
            groups=group_data,
            highest_avg=highest_avg,
            lowest_avg=lowest_avg,
            gap=gap,
            overall_avg=overall_avg
        )

    return render_template("index.html")


@app.route("/download")
def download():
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], "group_output.xlsx")
    return send_file(file_path, as_attachment=True)


if __name__ == "__main__":
    app.run(debug=True)
