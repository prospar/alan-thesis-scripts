import configparser
import csv
import sys


def makeConvSrc(params):
    with open(params['name'] + '.c', 'w') as srcfile:
        print(params['name'])
        srcfile.write("#include <stdio.h>\n")
        srcfile.write("#include <stdlib.h>\n")
        srcfile.write("\n")
        srcfile.write("#define _mb " + str(params['mb']) + "\n")
        srcfile.write("#define _nb " + str(params['nb']) + "\n")
        srcfile.write("#define _m " + str(params['bq']) + "\n")
        srcfile.write("#define _n " + str(params['bk']) + "\n")
        srcfile.write("#define _k " + str(params['bc']) + "\n")
        srcfile.write("#define _N " + str(params['N']) + "\n")
        srcfile.write("#define _C " + str(params['C']) + "\n")
        srcfile.write("#define _H " + str(params['H']) + "\n")
        srcfile.write("#define _W " + str(params['W']) + "\n")
        srcfile.write("#define _R " + str(params['R']) + "\n")
        srcfile.write("#define _S " + str(params['S']) + "\n")
        srcfile.write("#define _K " + str(params['K']) + "\n")
        srcfile.write("#define _P " + str(params['P']) + "\n")
        srcfile.write("#define _Q " + str(params['Q']) + "\n")
        srcfile.write("#define _Cb (_C / _k)\n")
        srcfile.write("#define _Kb (_K / _n)\n")
        srcfile.write("#define _Qb (_Q / _m)\n")
        srcfile.write("\n\n")

        srcfile.write("float INPUT[_N][_Cb][_H][_W][_k];\n")
        srcfile.write("float WEIGHT[_Kb][_Cb][_R][_S][_k][_n];\n")
        srcfile.write("float OUTPUT[_N][_Kb][_P][_Q][_n];\n")
        srcfile.write("\n")

        for i in range(params['mb']):
            for j in range(params['nb']):
                varname = "acc_reg_" + str(i) + "_" + str(j)
                srcfile.write("float " + varname + ";\n")
        srcfile.write("\n")

        srcfile.write("int main() {\n")
        srcfile.write("#pragma scop\n")

        bi = 0
        for brgemm in params['BRGEMM']:
            bi += 1
            srcfile.write("// BRGEMM " + str(bi) + " begins\n")
            srcfile.write("#define c_" + str(bi) + "_0 " + str(brgemm['C'][0]) + "\n")
            srcfile.write("#define c_" + str(bi) + "_1 " + str(brgemm['C'][1]) + "\n")
            srcfile.write("#define c_" + str(bi) + "_2 " + str(brgemm['C'][2]) + "\n")
            srcfile.write("#define c_" + str(bi) + "_3 " + str(brgemm['C'][3]) + "\n")
            srcfile.write("#define c_" + str(bi) + "_4 " + str(brgemm['C'][4]) + "\n")

            srcfile.write("\tfor (int im = 0; im < _m; im += _mb) {\n")
            srcfile.write("\t\tfor (int in = 0; in < _n; in += _nb) {\n")

            for i in range(params['mb']):
                for j in range(params['nb']):
                    lhs = "acc_reg_" + str(i) + "_" + str(j)
                    rhs0 = "c_" + str(bi) + "_0"
                    rhs1 = "c_" + str(bi) + "_1"
                    rhs2 = "c_" + str(bi) + "_2"
                    rhs3 = "c_" + str(bi) + "_3 + im + " + str(i)
                    rhs4 = "c_" + str(bi) + "_4 + in + " + str(j)
                    rhs = "OUTPUT["+rhs0+"]["+rhs1+"]["+rhs2+"]["+rhs3+"]["+rhs4+"]"
                    srcfile.write("\t\t\t" + lhs + " = " + rhs + ";\n")
            srcfile.write("\n")

            for batch in range(brgemm['Batches']):
                a0 = str(brgemm['A'][batch][0])
                a1 = str(brgemm['A'][batch][1])
                a2 = str(brgemm['A'][batch][2])
                a3 = str(brgemm['A'][batch][3])
                a4 = str(brgemm['A'][batch][4])
                a5 = str(brgemm['A'][batch][5])

                b0 = str(brgemm['B'][batch][0])
                b1 = str(brgemm['B'][batch][1])
                b2 = str(brgemm['B'][batch][2])
                b3 = str(brgemm['B'][batch][3])
                b4 = str(brgemm['B'][batch][4])

                srcfile.write("\t\t\tfor (int ik = 0; ik < _k; ++ik) {\n")

                for i in range(params['mb']):
                    for j in range(params['nb']):
                        lhs = "acc_reg_" + str(i) + "_" + str(j)
                        _a4 = a4 + " + " + str(i)
                        _a5 = a5 + " + ik"
                        a = "WEIGHT["+a0+"]["+a1+"]["+a2+"]["+a3+"]["+_a4+"]["+_a5+"]"
                        _b3 = b3 + " + ik"
                        _b4 = b4 + " + " + str(j)
                        b = "INPUT["+b0+"]["+b1+"]["+b2+"]["+_b3+"]["+_b4+"]"

                        srcfile.write("\t\t\t\t" + lhs + "+=" + a + " * " + b + ";\n" )

                srcfile.write("\t\t\t}\n")

            for i in range(params['mb']):
                for j in range(params['nb']):
                    rhs = "acc_reg_" + str(i) + "_" + str(j)
                    lhs0 = "c_" + str(bi) + "_0"
                    lhs1 = "c_" + str(bi) + "_1"
                    lhs2 = "c_" + str(bi) + "_2"
                    lhs3 = "c_" + str(bi) + "_3 + im + " + str(i)
                    lhs4 = "c_" + str(bi) + "_4 + in + " + str(j)
                    lhs = "OUTPUT["+rhs0+"]["+rhs1+"]["+rhs2+"]["+rhs3+"]["+rhs4+"]"
                    srcfile.write("\t\t\t" + lhs + " = " + rhs + ";\n")
            srcfile.write("\n")

            srcfile.write("\t\t}\n")
            srcfile.write("\t}\n")

            srcfile.write("// BRGEMM " + str(bi) + " ends\n")

        srcfile.write("#pragma endscop\n")
        srcfile.write("}\n")


def calcBRGEMMParams(params):
    Cb = int(params['C'] / params['bc'])
    Kb = int(params['K'] / params['bk'])
    Qb = int(params['Q'] / params['bq'])

    brgemms = []
    for n in range(params['N']):
        for kb in range(Kb):
            for cb in range(0, Cb, params['B_c']):
                for oj in range(params['P']):
                    for oib in range(Qb):
                        oi = oib * params['bq']
                        ii = params['str'] * oi
                        ij = params['str'] * oj
                        brgemmParams = {'A' : [], 'B' : []}

                        for r in range(params['R']):
                            for s in range(params['S']):
                                for c in range(params['B_c']):
                                    Apos = [kb, cb + c, r, s, 0, 0]
                                    Bpos = [n, cb + c, ij + r, ii + s, 0]
                                    brgemmParams['A'].append(Apos)
                                    brgemmParams['B'].append(Bpos)

                        brgemmParams['C'] = [n, kb, oj, oi, 0]
                        brgemmParams['Batches'] = len(brgemmParams['A'])
                        brgemms.append(brgemmParams)

    return brgemms


if __name__ == "__main__":
    bfile = sys.argv[1]
    mode = sys.argv[2]
    config = configparser.ConfigParser()
    config.read("convopts.cfg")
    config = config[mode]
    bc = int(config['bc'])
    bk = int(config['bk'])
    bq = int(config['bq'])
    B_c = int(config['B_c'])
    mb = int(config['mb'])
    nb = int(config['nb'])

    with open(bfile, 'r') as bench:
        reader = csv.DictReader(bench)
        for row in reader:
            params = {
                'name' : row["Layer name"],
                'N' : 1,
                'C' : int(row[" Channels"].strip()),
                'H' : int(row[" IFMAP Height"].strip()),
                'W' : int(row[" IFMAP Width"].strip()),
                'R' : int(row[" Filter Height"].strip()),
                'S' : int(row[" Filter Width"].strip()),
                'K' : int(row[" Num Filter"].strip()),
                'str' : int(row[" Strides"].strip())
            }

            params['P'] = int(params['H'] / params['str'])
            params['Q'] = int(params['W'] / params['str'])

            params['bc'] = bc
            params['bk'] = bk
            params['bq'] = bq
            params['B_c'] = B_c
            params['mb'] = mb
            params['nb'] = nb

            params['BRGEMM'] = calcBRGEMMParams(params)
            makeConvSrc(params)

