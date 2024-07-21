from flask import Flask, request, jsonify

app = Flask(__name__)


@app.route('/process', methods=['POST'])
def process_input():
    cmd = request.json['content']

    # 这里处理输入数据，使用loaded_data
    # 示例：简单地将输入内容转为大写
    import re

    def plain2pd_expr(d_conditions: list, logic: list) -> str:
        def fun(d_condition):
            if d_condition['op'] == '=':
                d_condition['op'] = '=='
            if d_condition['key'] == 'Quarter':
                return f"(data['Quarter']{d_condition['op']}'{d_condition['val']}')"
            return f"(data['{d_condition['key']}']{d_condition['op']}{d_condition['val']})"

        if not logic:
            return fun(d_conditions[0])
        if logic[0] == 'AND':
            return fun(d_conditions[0]) + '&' + fun(d_conditions[1])
        return fun(d_conditions[0]) + '|' + fun(d_conditions[1])

    def extract(d_conditions, logic: list):
        import pickle
        with open('JCR2024.pkl', 'rb') as f:
            data = pickle.load(f)
        log = f'记录中共有{data.shape[0]}本期刊。'
        # 过滤掉ISSN和IF缺失的期刊
        data.dropna(subset=[expr['key'] for expr in d_conditions], how='any', inplace=True)
        log += f'\n去除掉缺失的期刊后，还剩{data.shape[0]}本期刊。'
        expr = plain2pd_expr(d_conditions, logic)
        data = data[eval(expr)]
        log += f'\n满足条件的期刊，有{data.shape[0]}本。'
        # 提取这些期刊的ISSN，用 OR 连接
        issns = ' OR '.join(data['ISSN'].to_list())
        return issns, log

    op_relation = '(' + '|'.join(['>=', '<=', '>', '<', '=']) + ')'
    keys = ['IF-2023', 'IF-5Y', 'Quarter']
    logic = re.findall(r'(AND|OR)', cmd)
    log = ''
    if len(logic) > 1:
        # raise RuntimeError('只能输入一个逻辑连结词！')
        log += '\n只能输入一个逻辑连结词！'
        res = ''
        return jsonify({"result": res, "log": log})
    if len(logic) == 1:
        statements = [each.strip() for each in cmd.split(logic[0])]
    else:
        statements = [cmd.strip()]
    conditions = []
    for statement in statements:
        cond = dict()
        op = re.findall(op_relation, statement)
        if len(op) > 1:
            # raise RuntimeError('非法逻辑表达式！')
            log += '\n非法逻辑表达式！'
            res = ''
            return jsonify({"result": res, "log": log})
        op = op[0]
        cond['op'] = op
        parts = [each.strip() for each in statement.split(op)]
        if len(parts) != 2:
            # raise RuntimeError('非法逻辑表达式！')
            log += '\n非法逻辑表达式！'
            res = ''
            return jsonify({"result": res, "log": log})
        if parts[0] not in keys:
            # raise RuntimeError('关系操作符左侧应为IF-2023或IF-5Y或Quarter')
            log += '\n关系操作符左侧应为IF-2023或IF-5Y或Quarter'
            res = ''
            return jsonify({"result": res, "log": log})
        cond['key'] = parts[0]
        cond['val'] = parts[1]
        conditions.append(cond)
    # print(conditions)
    res, log_ = extract(conditions, logic)
    log += log_

    return jsonify({"result": res, "log": log})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80)  # 注意这里端口改为80
