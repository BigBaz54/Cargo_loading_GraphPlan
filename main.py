from graphplan import GraphPlan


def DoPlan(r_ops, r_facts):
    gp = GraphPlan(r_facts)
    _ = gp.graphplan()
    gp.write_trace()


if __name__ == '__main__':
    r_ops = 'examples/r_ops.txt'
    r_facts = 'examples/my_r_fact9.txt'

    DoPlan(r_ops, r_facts)