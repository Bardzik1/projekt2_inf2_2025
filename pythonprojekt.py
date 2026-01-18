import sys
from PyQt5.QtWidgets import QApplication, QFormLayout, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QSpinBox, QDoubleSpinBox
from PyQt5.QtCore import QTimer, Qt, QRectF, QPointF
from PyQt5.QtGui import QPainter, QBrush, QPen, QColor, QPainterPath

class Rura:
    def __init__(self, punkty, kolor_cieczy, grubosc=12, kolor_rury=Qt.black):
        self.punkty = [QPointF(float(p[0]), float(p[1])) for p in punkty]
        self.grubosc = grubosc
        self.kolor_rury = kolor_rury
        self.czy_plynie = False
        self.kolor_cieczy = kolor_cieczy

    def ustaw_przeplyw(self, plynie):
        self.czy_plynie = plynie

    def draw(self, painter):
        if len(self.punkty) < 2:
            return

        path = QPainterPath()
        path.moveTo(self.punkty[0])
        for p in self.punkty[1:]:
            path.lineTo(p)

            #Rysowanie rury
        pen_rura = QPen(self.kolor_rury, self.grubosc, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
        painter.setPen(pen_rura)
        painter.setBrush(Qt.NoBrush)
        painter.drawPath(path)

        #Rysowanie cieczy w rurze
        if self.czy_plynie:
            pen_ciecz = QPen(self.kolor_cieczy, self.grubosc - 4, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
            painter.setPen(pen_ciecz)
            painter.drawPath(path)


class Zbiornik:
    def __init__ (self, x, y, kolor_zbiornik, temp, width=100, height=140, nazwa=""):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.pojemnosc = 100.0
        self.aktualna_ilosc = 0.0
        self.poziom = 0.0
        self.kolor_zbiornik = kolor_zbiornik
        self.nazwa = nazwa
        self.grzalka = False
        self.temp = temp
        self.pokaz_temp = False
       

    def dodaj_ciecz(self, ilosc):
        wolne = self.pojemnosc - self.aktualna_ilosc
        dodano = min(ilosc, wolne)
        self.aktualna_ilosc += dodano
        self.aktualizuj_poziom()
        return dodano

    def usun_ciecz(self, ilosc):
        usunieto = min(ilosc, self.aktualna_ilosc)
        self.aktualna_ilosc -= usunieto
        self.aktualizuj_poziom()
        return usunieto
   
    def aktualizuj_poziom(self):
        self.poziom = self.aktualna_ilosc / self.pojemnosc

    def czy_pusty(self):
        return self.aktualna_ilosc <= 0.1

    def czy_pelny(self):
        return self.aktualna_ilosc >= self.pojemnosc - 0.1

    def gora(self):
        return (self.x + self.width/2, self.y)

    def dol(self):
        return(self.x + self.width/2, self.y + self.height)

    def draw(self, painter):
        #rysowanie cieczy w zbiorniku
        if self.poziom > 0:
            h_cieczy = self.height * self.poziom
            y_start = self.y + self.height - h_cieczy
            painter.setPen(Qt.NoPen)
            painter.setBrush(self.kolor_zbiornik)
            painter.drawRect(int(self.x + 3), int(y_start), int(self.width - 6), int(h_cieczy - 2))

        #rysowanie ramki zbiornika
        pen = QPen(Qt.white, 4)
        pen.setJoinStyle(Qt.MiterJoin)
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)
        painter.drawRect (int(self.x), int(self.y), int(self.width), int(self.height))

        #Podpis zbiornika i aktualna temperatura
        painter.setPen(Qt.white)
        painter.drawText(int(self.x + self.width + 30), int(self.y + 50), self.nazwa)
        temp_tekst = f"{self.temp:.1f} C"
        if self.pokaz_temp == True:
            painter.drawText(int(self.x + self.width + 30), int(self.y + 100), temp_tekst)

        #rysowanie grzalki w zaleznosci od parametru self.grzalka
        if self.grzalka == True:
            if self.czy_pelny():
                pen = QPen(Qt.black, 2, Qt.SolidLine)
                painter.setPen(pen)
                painter.setBrush(QBrush(QColor(255, 0, 0, 180), Qt.SolidPattern))
                painter.drawEllipse(int(self.x + self.width/2 - 15), int(self.y + 100), 30, 30)


class Symulacja(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Browar - symulacja w stylu SCADA")
        self.setFixedSize(900, 600)
        self.setStyleSheet("background-color: #A0A0A0;")

        self.z1 = Zbiornik(50, 80, QColor(0, 180, 255), 20.0, nazwa="Zbiornik wody")
        self.z1.aktualna_ilosc = 100.0
        self.z1.pokaz_temp = True
        self.z1.aktualizuj_poziom()

        self.z2 = Zbiornik(350, 80, QColor(218, 165, 32), 0.0, nazwa="Kadz")
        self.z2.grzalka = True
        self.z2.pokaz_temp = True
        self.z2.aktualizuj_poziom()

        self.z3 = Zbiornik(650, 80, QColor(139, 69, 19), 0.0, nazwa="Kociol")
        self.z3.grzalka = True
        self.z3.pokaz_temp = True
        self.z3.aktualizuj_poziom()

        self.z4 = Zbiornik(650,400, QColor(255, 215, 0), 1.0, nazwa="Fermentor")
        self.z4.aktualizuj_poziom()

        self.z2_otwarty = False
        self.z3_otwarty = False

        self.zbiorniki = [self.z1, self.z2, self.z3, self.z4]

        self.btn = QPushButton("Start / Stop")
        self.btn.setFixedSize(100, 30)
        self.btn.setStyleSheet("background-color: #444; color: white;")
        self.btn.clicked.connect(self.przelacz_symulacje)

        self.btn2 = QPushButton("Reset")
        self.btn2.setFixedSize(100, 30)
        self.btn2.setStyleSheet("background-color: #444; color: white;")
        self.btn2.clicked.connect(self.reset_symulacji)

        #zestawy qformlayout - qlabel + qwidget do opisania wartosci zmienianej przez uzytkownika oraz panel wpisywania
        temperatura_layout = QFormLayout()
        self.input_temp_z1 = QSpinBox()
        self.input_temp_z1.setRange(0, 90)
        self.input_temp_z1.setValue(20)
        self.input_temp_z1.setFixedWidth(60)
        temperatura_layout.addRow("T0 z1: ", self.input_temp_z1)

        self.input_grzalka1 = QDoubleSpinBox()
        self.input_grzalka1.setRange(0.01, 1)
        self.input_grzalka1.setValue(0.5)
        self.input_grzalka1.setFixedWidth(60)
        temperatura_layout.addRow("Moc grzalki 1: ", self.input_grzalka1)

        self.input_grzalka2 = QDoubleSpinBox()
        self.input_grzalka2.setRange(0.01, 1)
        self.input_grzalka2.setValue(0.1)
        self.input_grzalka2.setFixedWidth(60)
        temperatura_layout.addRow("Moc grzalki 2", self.input_grzalka2)

        self.input_flow_speed = QDoubleSpinBox()
        self.input_flow_speed.setRange(0.1, 5)
        self.input_flow_speed.setValue(0.7)
        self.input_flow_speed.setFixedWidth(60)
        temperatura_layout.addRow("Predkosc przeplywu", self.input_flow_speed)

        #uporzadkowanie przyciskow i pol zmiennych
        panel = QHBoxLayout()
        panel.setContentsMargins(20, 10, 20, 10)
        panel.addWidget(self.btn)
        panel.addSpacing(10)
        panel.addWidget(self.btn2)
        panel.addSpacing(30)
        panel.addLayout(temperatura_layout)
        panel.addStretch()

        glowny_layout = QVBoxLayout()
        glowny_layout.addStretch(1)
        glowny_layout.addLayout(panel)

        self.setLayout(glowny_layout)

        #polaczenia miedzy zbiornikami - zakrety 90 stopni
        p_start = self.z1.dol()
        p_koniec = self.z2.gora()
        mid_y_dol1 = self.z1.height + self.z1.height + 50
        mid_y_gora1 = self.z1.y - 50

        self.rura1 = Rura([p_start, (self.z1.x + self.z1.width/2, mid_y_dol1), (self.z1.x + self.z1.width/2 + 200, mid_y_dol1),(self.z1.x + self.z1.width/2 + 200, mid_y_gora1),(p_koniec[0], mid_y_gora1),  p_koniec], QColor(0, 180, 255))

        p_start2 = self.z2.dol()
        p_koniec2 = self.z3.gora()
        self.rura2 = Rura([p_start2, (self.z2.x + self.z2.width/2, mid_y_dol1), (self.z2.x + self.z2.width/2 + 200, mid_y_dol1), (self.z2.x + self.z2.width/2 + 200, mid_y_gora1), (p_koniec2[0], mid_y_gora1), p_koniec2], QColor(139, 69, 19))

        p_start3 = self.z3.dol()
        p_koniec3 = self.z4.gora()
       
        self.rura3 = Rura([p_start3, p_koniec3], QColor(255, 215, 0))

        self.rury = [self.rura1, self.rura2, self.rura3]

        self.timer = QTimer()
        self.timer.timeout.connect(self.logika_przeplywu)

        self.running = False


    def przelacz_symulacje(self):
        if self.running:
            self.timer.stop()

            #Odblokowane parametry do zmiany podczas zatrzymania animacji
            self.input_temp_z1.setEnabled(True)
            self.input_grzalka1.setEnabled(True)
            self.input_grzalka2.setEnabled(True)
            self.input_flow_speed.setEnabled(True)

        else:
            self.timer.start(20)

            #Zablokowana zmiana parametrow podczas animacji w toku
            self.input_temp_z1.setEnabled(False)
            self.input_grzalka1.setEnabled(False)
            self.input_grzalka2.setEnabled(False)
            self.input_flow_speed.setEnabled(False)
        self.running = not self.running

        #funkcja resetowania; mozliwosc zmiany parametrow po resecie
    def reset_symulacji(self):

        self.z1.temp = self.input_temp_z1.value()
        self.z1.aktualna_ilosc = 100.0
        self.z1.aktualizuj_poziom()

        self.z2.aktualna_ilosc = 0.0
        self.z2.temp = 0.0
        self.z2.kolor_zbiornik = QColor(218, 165, 32)
        self.z2.aktualizuj_poziom()

        self.z3.aktualna_ilosc = 0.0
        self.z3.temp = 0.0
        self.z3.kolor_zbiornik = QColor(139, 69, 19)
        self.z3.aktualizuj_poziom()

        self.z4.aktualna_ilosc = 0.0
        self.z4.aktualizuj_poziom()

        if self.running:
            self.timer.stop()
            self.running = False

        self.input_temp_z1.setEnabled(True)
        self.input_grzalka1.setEnabled(True)
        self.input_grzalka2.setEnabled(True)
        self.input_flow_speed.setEnabled(True)
           
        for r in self.rury:
            r.czy_plynie = False

        self.z2_otwarty = False
        self.z3_otwarty = False

        self.update()


    def logika_przeplywu(self):

        if self.z2.czy_pelny():
            self.z2_otwarty = True
        elif self.z2.czy_pusty():
            self.z2_otwarty = False

        if self.z3.czy_pelny():
            self.z3_otwarty = True
        elif self.z3.czy_pusty():
            self.z3_otwarty = False

        t = self.z1.temp
        plynie_1 = False
        plynie_2 = False
        plynie_3 = False
        g1 = self.input_grzalka1.value()
        g2 = self.input_grzalka2.value()
        self.flow_speed = self.input_flow_speed.value()

        if not self.z1.czy_pusty() and not self.z2.czy_pelny():
            ilosc = self.z1.usun_ciecz(self.flow_speed)
            self.z2.dodaj_ciecz(ilosc)
            plynie_1 = True
            self.z2.temp = t
            plynie_1 = True
        self.rura1.ustaw_przeplyw(plynie_1)

        if self.z2.czy_pelny() and self.z2.temp < 78.0:
            self.z2.temp=self.z2.temp + g1
            if self.z2.temp >78:
                self.z2.temp = 78

        if self.z2.temp == 78.0:
            self.z2.kolor_zbiornik = QColor(139, 69, 19)

        #dopoki ciecz (przyszle piwo) nie osiagnie temperatury 78 stopni w kadzi nie zostanie wypuszczone do kotla
        if self.z2_otwarty and self.z2.temp == 78.0 and not self.z3.czy_pelny():
            ilosc = self.z2.usun_ciecz(self.flow_speed)
            self.z3.dodaj_ciecz(ilosc)
            plynie_2 = True
            self.z3.temp = self.z2.temp
            plynie_2 = True
        self.rura2.ustaw_przeplyw(plynie_2)

        if self.z3.czy_pelny() and self.z3.temp <100.0:
            self.z3.temp=self.z3.temp + g2
            if self.z3.temp > 100:
                self.z3.temp = 100

        if self.z3.temp == 100.0:
            self.z3.kolor_zbiornik = QColor(255, 215, 0)

        #dopoki ciecz(przyszle piwo) nie osiagnie 100 stopni w kadzi nie moze plynac dalej do fermentatora pofermentowac i zamienic sie w piwko
        if self.z3_otwarty and not self.z4.czy_pelny() and self.z3.temp == 100.0:
            ilosc = self.z3.usun_ciecz(self.flow_speed)
            self.z4.dodaj_ciecz(ilosc)
            plynie_3 = True
        self.rura3.ustaw_przeplyw(plynie_3)

        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)

        for r in self.rury: r.draw(p)
        for z in self.zbiorniki: z.draw(p)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    okno = Symulacja()
    okno.show()
    sys.exit(app.exec_())
