import sys
import os
import pandas as pd
import pywhatkit
import time
from datetime import datetime

from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton, QLabel, QFileDialog,
    QTextEdit, QListWidget, QMessageBox, QProgressBar, QDialog, QTextBrowser, QCheckBox
)
from PyQt5.QtGui import QFont, QColor
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QPropertyAnimation, QEasingCurve, pyqtProperty

LOG_FILE = "log_envio_whatsapp.txt"

class EnvioThread(QThread):
    progresso = pyqtSignal(int)
    mensagem_status = pyqtSignal(str)
    envio_finalizado = pyqtSignal(float, str, str)

    def __init__(self, contatos, mensagem, usar_nominal):
        super().__init__()
        self.contatos = contatos
        self.mensagem = mensagem
        self.usar_nominal = usar_nominal

    def run(self):
        total = len(self.contatos)
        inicio = datetime.now()
        with open(LOG_FILE, "w", encoding="utf-8") as log_file:
            log_file.write(f"Envio iniciado: {inicio.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            for i, contato in enumerate(self.contatos):
                try:
                    numero_bruto = str(contato['Telefone']).strip()
                    numero = ''.join(filter(str.isdigit, numero_bruto))
                    numero = f"+{numero}"

                    nome = contato.get("Nome", "Desconhecido")

                    mensagem_final = f"{nome}, {self.mensagem}" if self.usar_nominal else self.mensagem

                    status_msg = f"Enviando para {nome} ({numero})"
                    self.mensagem_status.emit(status_msg)
                    log_file.write(status_msg + "\n")

                    pywhatkit.sendwhatmsg_instantly(numero, mensagem_final, wait_time=15, tab_close=True)

                    success_msg = f"✅ Enviado com sucesso: {nome} ({numero})"
                    self.mensagem_status.emit(success_msg)
                    log_file.write(success_msg + "\n")

                    time.sleep(10)

                except Exception as e:
                    error_msg = f"❌ Erro ao enviar para {contato['Telefone']}: {e}"
                    self.mensagem_status.emit(error_msg)
                    log_file.write(error_msg + "\n")

                progresso_atual = int(((i + 1) / total) * 100)
                self.progresso.emit(progresso_atual)

            fim = datetime.now()
            duracao = (fim - inicio).total_seconds()
            log_file.write(f"\nEnvio finalizado: {fim.strftime('%Y-%m-%d %H:%M:%S')}\n")
            log_file.write(f"Tempo total de envio: {duracao:.2f} segundos\n")

        self.envio_finalizado.emit(duracao, inicio.strftime('%H:%M:%S'), fim.strftime('%H:%M:%S'))

class AnimatedButton(QPushButton):
    def __init__(self, *args, normal_color="#4a90e2", hover_color="#357ABD", pressed_color="#2a5d9f", **kwargs):
        super().__init__(*args, **kwargs)
        self._normal_color = QColor(normal_color)
        self._hover_color = QColor(hover_color)
        self._pressed_color = QColor(pressed_color)
        self._current_color = self._normal_color

        self._animation = QPropertyAnimation(self, b"color")
        self._animation.setDuration(300)
        self._animation.setEasingCurve(QEasingCurve.InOutQuad)

        self.setStyleSheet(self._build_stylesheet(self._normal_color))

    def enterEvent(self, event):
        self.animate_color(self._hover_color)
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.animate_color(self._normal_color)
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        self.setStyleSheet(self._build_stylesheet(self._pressed_color))
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        if self.underMouse():
            self.animate_color(self._hover_color)
        else:
            self.animate_color(self._normal_color)
        super().mouseReleaseEvent(event)

    def animate_color(self, target_color):
        self._animation.stop()
        self._animation.setStartValue(self._current_color)
        self._animation.setEndValue(target_color)
        self._animation.start()
        self._current_color = target_color

    def getColor(self):
        return self._current_color

    def setColor(self, color):
        if isinstance(color, QColor):
            self._current_color = color
            self.setStyleSheet(self._build_stylesheet(color))

    color = pyqtProperty(QColor, fget=getColor, fset=setColor)

    def _build_stylesheet(self, color: QColor):
        return f"""
            QPushButton {{
                background-color: {color.name()};
                border: none;
                border-radius: 6px;
                padding: 10px 20px;
                color: white;
                font-weight: 600;
            }}
        """

class WhatsAppSender(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Envio automático de mensagens")
        self.setGeometry(300, 100, 600, 700)

        self.layout = QVBoxLayout()

        self.label_titulo = QLabel("Envio automático de mensagens")
        self.label_titulo.setFont(QFont("Segoe UI", 20, QFont.Bold))
        self.layout.addWidget(self.label_titulo, alignment=Qt.AlignCenter)

        self.botao_carregar = AnimatedButton("Carregar CSV")
        self.layout.addWidget(self.botao_carregar)
        self.botao_carregar.clicked.connect(self.carregar_csv)

        self.lista_contatos = QListWidget()
        self.lista_contatos.setStyleSheet("""
            QListWidget {
                background-color: white;
                border: 1px solid #d1d9e6;
                border-radius: 6px;
                padding: 6px;
            }
            QListWidget::item {
                padding: 8px;
                border-radius: 4px;
            }
            QListWidget::item:selected {
                background-color: #0057b7;
                color: white;
                font-weight: 600;
            }
        """)
        self.layout.addWidget(self.lista_contatos)

        self.botao_remover = AnimatedButton("Remover Selecionado", normal_color="#e74c3c", hover_color="#c0392b", pressed_color="#962d22")
        self.layout.addWidget(self.botao_remover)
        self.botao_remover.clicked.connect(self.remover_selecionado)

        self.checkbox_nominal = QCheckBox("Adicionar nome na mensagem (Nominal)")
        self.layout.addWidget(self.checkbox_nominal)

        self.texto_mensagem = QTextEdit()
        self.texto_mensagem.setPlaceholderText("Digite sua mensagem aqui...")
        self.texto_mensagem.setStyleSheet("""
            QTextEdit {
                background-color: white;
                border: 1px solid #d1d9e6;
                border-radius: 6px;
                padding: 10px;
                font-size: 14px;
                color: #333333;
            }
        """)
        self.layout.addWidget(self.texto_mensagem)

        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(True)
        self.layout.addWidget(self.progress_bar)

        self.botao_enviar = AnimatedButton("Enviar Mensagens", normal_color="#27ae60", hover_color="#1e8449", pressed_color="#14532d")
        self.layout.addWidget(self.botao_enviar)
        self.botao_enviar.clicked.connect(self.iniciar_envio)

        self.botao_log = AnimatedButton("Ver Registro de Envio")
        self.layout.addWidget(self.botao_log)
        self.botao_log.clicked.connect(self.ver_log_envio)

        self.setLayout(self.layout)

        self.setStyleSheet("""
            QWidget {
                background-color: #f5f7fa;
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                font-size: 13px;
                color: #333333;
            }
            QLabel {
                font-size: 20px;
                font-weight: 700;
                color: #1a1a1a;
                margin-bottom: 20px;
            }
            QProgressBar {
                border: 1px solid #bbb;
                border-radius: 6px;
                text-align: center;
                color: #333;
                background-color: #e6e6e6;
            }
            QProgressBar::chunk {
                background-color: #4a90e2;
                border-radius: 6px;
            }
        """)

        self.contatos = []

    def carregar_csv(self):
        path, _ = QFileDialog.getOpenFileName(self, "Selecionar CSV", "", "Arquivos CSV (*.csv)")
        if path:
            try:
                df = pd.read_csv(path, sep=',')
                if "Telefone" not in df.columns or "Nome" not in df.columns:
                    df = pd.read_csv(path, sep=';')
                    if "Telefone" not in df.columns or "Nome" not in df.columns:
                        QMessageBox.warning(self, "Erro", "O CSV deve conter colunas 'Nome' e 'Telefone'")
                        return
                self.contatos = df.to_dict("records")
                self.lista_contatos.clear()
                for c in self.contatos:
                    self.lista_contatos.addItem(f"{c['Nome']} - {c['Telefone']}")
            except Exception as e:
                QMessageBox.critical(self, "Erro", f"Erro ao carregar CSV: {e}")

    def remover_selecionado(self):
        for item in self.lista_contatos.selectedItems():
            row = self.lista_contatos.row(item)
            self.lista_contatos.takeItem(row)
            del self.contatos[row]

    def iniciar_envio(self):
        if not self.contatos:
            QMessageBox.warning(self, "Atenção", "Nenhum contato carregado")
            return
        mensagem = self.texto_mensagem.toPlainText().strip()
        if not mensagem:
            QMessageBox.warning(self, "Atenção", "Digite uma mensagem")
            return

        usar_nominal = self.checkbox_nominal.isChecked()

        self.thread = EnvioThread(self.contatos, mensagem, usar_nominal)
        self.thread.progresso.connect(self.progress_bar.setValue)
        self.thread.mensagem_status.connect(lambda msg: print(msg))
        self.thread.envio_finalizado.connect(self.mostrar_finalizacao)
        self.thread.start()

    def mostrar_finalizacao(self, duracao, inicio, fim):
        QMessageBox.information(
            self,
            "Finalizado",
            f"Todas as mensagens foram enviadas.\n\n"
            f"Início: {inicio}\n"
            f"Fim: {fim}\n"
            f"Tempo total: {duracao:.2f} segundos\n\n"
            f"Consulte o log de envio para detalhes."
        )

    def ver_log_envio(self):
        if not os.path.exists(LOG_FILE):
            QMessageBox.information(self, "Log", "Nenhum envio realizado ainda.")
            return

        with open(LOG_FILE, "r", encoding="utf-8") as f:
            log_text = f.read()

        dialog = QDialog(self)
        dialog.setWindowTitle("Registro de Envio")
        layout = QVBoxLayout()
        log_view = QTextBrowser()
        log_view.setText(log_text)
        layout.addWidget(log_view)
        dialog.setLayout(layout)
        dialog.resize(600, 400)
        dialog.exec_()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    janela = WhatsAppSender()
    janela.show()
    sys.exit(app.exec_())

