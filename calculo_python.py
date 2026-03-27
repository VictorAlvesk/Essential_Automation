consumo = 500
abatimento = 300
saldo = 1000
mes = 0

while saldo > 0:
    abate = consumo - abatimento
    saldo = saldo - abate
    mes += 1

print(mes)
