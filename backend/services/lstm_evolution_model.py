import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
import logging
import os

logger = logging.getLogger(__name__)

class EvolutionLSTM(nn.Module):
    def __init__(self, input_size=2, hidden_size=32, num_layers=1, output_size=1):
        """
        Red Neuronal LSTM para predecir la evolución de severidad.
        Input: [Severidad, DíasDesdeInicio]
        Output: Severidad predicha para el siguiente paso.
        """
        super(EvolutionLSTM, self).__init__()
        self.hidden_size = hidden_size
        self.num_layers = num_layers
        
        # LSTM Layer
        self.lstm = nn.LSTM(input_size, hidden_size, num_layers, batch_first=True)
        
        # Fully Connected Layer
        self.fc = nn.Linear(hidden_size, output_size)
    
    def forward(self, x):
        # x shape: (batch_size, sequence_length, input_size)
        
        # Inicializar hidden state y cell state
        h0 = torch.zeros(self.num_layers, x.size(0), self.hidden_size).to(x.device)
        c0 = torch.zeros(self.num_layers, x.size(0), self.hidden_size).to(x.device)
        
        # Forward propagate LSTM
        out, _ = self.lstm(x, (h0, c0))
        
        # Decodificar el último estado oculto
        out = self.fc(out[:, -1, :])
        return out

class EvolutionModelManager:
    def __init__(self, model_path="backend/models/evolution_lstm.pth"):
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.model_path = model_path
        self.model = EvolutionLSTM().to(self.device)
        self.is_trained = False
        
        # Cargar pesos si existen, si no, entrenar
        if os.path.exists(self.model_path):
            self.load_model()
        else:
            logger.info("⚠️ No se encontró modelo LSTM pre-entrenado. Iniciando auto-entrenamiento con datos sintéticos...")
            self.train_on_synthetic_data()

    def load_model(self):
        try:
            self.model.load_state_dict(torch.load(self.model_path, map_location=self.device))
            self.model.eval()
            self.is_trained = True
            logger.info("✅ Modelo LSTM de evolución cargado correctamente.")
        except Exception as e:
            logger.error(f"❌ Error cargando modelo LSTM: {e}")

    def predict_next_month(self, history_data):
        """
        history_data: Lista de tuplas (severidad, dias_transcurridos)
        Retorna: Predicción de severidad a 30 días del último punto.
        """
        if not self.is_trained:
            logger.warning("El modelo no está entrenado. Retornando valor del último punto.")
            return history_data[-1][0]
            
        try:
            # Preparar datos: normalizar
            # Severidad 0-10 -> 0.0-1.0
            # Días: escalar por 365 para que no sean números gigantes
            
            sequence = []
            for sev, days in history_data:
                sequence.append([sev / 10.0, days / 365.0])
            
            input_tensor = torch.tensor([sequence], dtype=torch.float32).to(self.device)
            
            with torch.no_grad():
                prediction = self.model(input_tensor)
                
            predicted_severity = prediction.item() * 10.0
            return max(0, min(10, predicted_severity)) # Clamp 0-10
            
        except Exception as e:
            logger.error(f"Error en predicción LSTM: {e}")
            return history_data[-1][0]

    def train_on_synthetic_data(self):
        """
        Genera datos sintéticos de recuperaciones típicas y entrena el modelo.
        """
        logger.info("🏋️‍♂️ Generando datos sintéticos y entrenando LSTM...")
        
        # 1. Generar Datos Sintéticos
        X_train = []
        y_train = []
        
        # Casos: Lineal, Logarítmico (rápido inicio, luego lento), Estancado
        for _ in range(500):
            # Caso A: Recuperación Lineal Ideal (10 -> 0 en 12-24 meses)
            start_sev = np.random.uniform(5, 10)
            duration = np.random.uniform(12, 24) * 30 # días
            days = np.linspace(0, duration, num=10)
            sev = np.linspace(start_sev, 0, num=10)
            
            # Crear secuencias
            seq = [[s/10.0, d/365.0] for s, d in zip(sev[:-1], days[:-1])]
            target = sev[-1]/10.0
            
            X_train.append(seq)
            y_train.append(target)
            
        # Convertir a Tensores
        # Padding necesario si tuviéramos longitudes variables, aquí simplificamos con 9 pasos fijos
        # Para producción real usaríamos collate_fn y padding
        
        X_tensor = torch.tensor(X_train, dtype=torch.float32).to(self.device)
        y_tensor = torch.tensor(y_train, dtype=torch.float32).view(-1, 1).to(self.device)
        
        # 2. Entrenar
        criterion = nn.MSELoss()
        optimizer = optim.Adam(self.model.parameters(), lr=0.01)
        
        self.model.train()
        for epoch in range(100):
            optimizer.zero_grad()
            outputs = self.model(X_tensor)
            loss = criterion(outputs, y_tensor)
            loss.backward()
            optimizer.step()
            
            if epoch % 20 == 0:
                logger.info(f"Epoch {epoch}, Loss: {loss.item():.4f}")
                
        # 3. Guardar
        os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
        torch.save(self.model.state_dict(), self.model_path)
        self.is_trained = True
        self.model.eval()
        logger.info("✅ Modelo LSTM entrenado y guardado.")

# Instancia Lazy
_evolution_manager = None
def get_evolution_model():
    global _evolution_manager
    if _evolution_manager is None:
        _evolution_manager = EvolutionModelManager()
    return _evolution_manager
