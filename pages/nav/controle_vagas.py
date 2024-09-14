import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder, StandardScaler
import os

def run():
    """
    Função principal que executa a aplicação Streamlit para controle de vagas de emprego.
    Inclui funcionalidades para adicionar, excluir e visualizar vagas, além de treinar e
    realizar previsões com um modelo de Machine Learning.
    """
    
    st.title('Controle de Vagas de Emprego')

    def get_user_id():
        """
        Solicita ao usuário que insira seu nome para criar um identificador único.
        
        Returns:
            str: Nome do usuário, utilizado como ID para o arquivo CSV.
        """
        return st.text_input('Digite seu nome', 'seu nome')

    def load_data(user_id):
        """
        Carrega os dados de um arquivo CSV com base no ID do usuário. Se o arquivo não existir,
        cria um novo DataFrame e salva como CSV.

        Args:
            user_id (str): ID do usuário para determinar o nome do arquivo CSV.

        Returns:
            pd.DataFrame: DataFrame carregado ou criado com as colunas padrão.
        """
        file_path = f'{user_id}_vagas.csv'
        if not os.path.exists(file_path):
            df = pd.DataFrame(columns=['ID', 'Data da Candidatura', 'Vaga', 'Nome da Empresa', 'Link da vaga', 'Origem da Candidatura', 'Pessoas da empresa adicionadas', 'Linkedin da pessoa que mandei a mensagem', 'Ultimo contato pelo linkedin', 'Status'])
            df.to_csv(file_path, index=False)
        return pd.read_csv(file_path)

    def save_data(df, user_id):
        """
        Salva o DataFrame no arquivo CSV com base no ID do usuário.

        Args:
            df (pd.DataFrame): DataFrame a ser salvo.
            user_id (str): ID do usuário para determinar o nome do arquivo CSV.
        """
        df.to_csv(f'{user_id}_vagas.csv', index=False)

    def prepare_features(data):
        """
        Prepara as características (features) e o alvo (target) para o treinamento do modelo.
        Inclui a codificação das variáveis categóricas e a normalização dos dados.

        Args:
            data (pd.DataFrame): DataFrame contendo os dados das vagas.

        Returns:
            tuple: (X, y, scaler, X_columns) onde
                - X (np.array): Array de características normalizadas.
                - y (np.array): Array de alvos codificados.
                - scaler (StandardScaler): Objeto scaler usado para normalizar as características.
                - X_columns (Index): Colunas do DataFrame de características.
        """
        try:
            le_status = LabelEncoder()
            data['Status_encoded'] = le_status.fit_transform(data['Status'])
            
            data['Data da Candidatura'] = pd.to_datetime(data['Data da Candidatura'], format='%Y-%m-%d', errors='coerce')
            data = data.dropna(subset=['Data da Candidatura'])
            data['Data da Candidatura'] = data['Data da Candidatura'].map(datetime.toordinal)
            
            X = data[['Data da Candidatura', 'Vaga', 'Origem da Candidatura', 'Pessoas da empresa adicionadas', 'Linkedin da pessoa que mandei a mensagem', 'Ultimo contato pelo linkedin']]
            y = data['Status_encoded']
            
            X = pd.get_dummies(X, drop_first=True)
            X_columns = X.columns
            scaler = StandardScaler()
            X = scaler.fit_transform(X)
            
            return X, y, scaler, X_columns
        except Exception as e:
            st.error(f"Erro ao preparar os dados: {e}")
            return None, None, None, None

    def train_model(data):
        """
        Treina o modelo de RandomForestClassifier usando os dados fornecidos.
        Realiza validação cruzada para avaliar o desempenho do modelo.

        Args:
            data (pd.DataFrame): DataFrame contendo os dados das vagas.

        Returns:
            tuple: (model, scaler, X_columns) onde
                - model (RandomForestClassifier): Modelo treinado.
                - scaler (StandardScaler): Objeto scaler usado para normalizar as características.
                - X_columns (Index): Colunas do DataFrame de características.
        """
        X, y, scaler, X_columns = prepare_features(data)

        if X is None or y is None:
            return None, None, None

        if len(y) < 5:
            st.warning('Dados insuficientes para realizar a validação cruzada com 5 dobras. Adicione mais dados.')
            return None, None, None

        try:
            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
            model = RandomForestClassifier(n_estimators=100, random_state=42)
            model.fit(X_train, y_train)

            cv_dobras = min(5, len(y))
            scores = cross_val_score(model, X, y, cv=cv_dobras)
            st.write(f"Acurácia média do modelo: {scores.mean():.2f}")

            return model, scaler, X_columns
        except Exception as e:
            st.error(f"Erro ao treinar o modelo: {e}")
            return None, None, None

    def predict(model, scaler, X_columns):
        """
        Realiza a previsão usando o modelo treinado com base nos dados inseridos pelo usuário.

        Args:
            model (RandomForestClassifier): Modelo treinado.
            scaler (StandardScaler): Objeto scaler usado para normalizar as características.
            X_columns (Index): Colunas do DataFrame de características.
        """
        data_hoje = st.date_input('Data da Candidatura para Previsão', datetime.today())
        vaga_previsao = st.text_input('Vaga para Previsão')
        origem_candidatura_previsao = st.text_input('Origem da Candidatura')
        pessoas_adicionadas_previsao = st.text_input('Pessoas da empresa adicionadas')
        linkedin_previsao = st.text_input('Linkedin da pessoa que mandei a mensagem')
        ultimo_contato_previsao = st.text_input('Ultimo contato pelo linkedin')

        if st.button('Prever'):
            if not (vaga_previsao and origem_candidatura_previsao and pessoas_adicionadas_previsao and linkedin_previsao and ultimo_contato_previsao):
                st.warning('Preencha todos os dados para análise e previsão do modelo')
            else:
                try:
                    data_hoje_ordinal = datetime.toordinal(data_hoje)
                    input_features = pd.DataFrame([[data_hoje_ordinal, vaga_previsao, origem_candidatura_previsao, pessoas_adicionadas_previsao, linkedin_previsao, ultimo_contato_previsao]],
                                                columns=['Data da Candidatura', 'Vaga', 'Origem da Candidatura', 'Pessoas da empresa adicionadas', 'Linkedin da pessoa que mandei a mensagem', 'Ultimo contato pelo linkedin'])
                    
                    input_features = pd.get_dummies(input_features, drop_first=True)
                    input_features = input_features.reindex(columns=X_columns, fill_value=0)
                    input_features = scaler.transform(input_features)
                    
                    probabilidade = model.predict_proba(input_features)
                    
                    if probabilidade.shape[1] > 1:
                        probabilidade = probabilidade[0][1]
                    else:
                        probabilidade = probabilidade[0][0]
                    
                    if probabilidade > 0.50:
                        st.success(f"Você tem {probabilidade * 100:.2f}% de chance de obter sucesso. Resultado: Sucesso")
                    else:
                        st.warning(f"Você tem {probabilidade * 100:.2f}% de chance de obter sucesso. Resultado: Não desista")
                except Exception as e:
                    st.error(f"Erro ao realizar a previsão: {e}")

    st.subheader('Adicionar Nova Vaga')
    user_id = get_user_id()
    if not user_id:
        st.warning('Por favor, insira um ID de usuário para continuar.')
        return

    df = load_data(user_id)

    with st.form(key='add_vaga_form'):
        id_vaga = st.text_input('ID da Vaga')
        data_candidatura = st.date_input('Data da Candidatura')
        vaga = st.text_input('Vaga')
        nome_empresa = st.text_input('Nome da Empresa')
        link_vaga = st.text_input('Link da Vaga')
        origem_candidatura = st.text_input('Origem da Candidatura')
        pessoas_adicionadas = st.text_input('Pessoas da empresa adicionadas')
        linkedin_mensagem = st.text_input('Linkedin da pessoa que mandei a mensagem')
        ultimo_contato = st.text_input('Ultimo contato pelo linkedin')
        status = st.selectbox('Status', ['Aguardando', 'Entrevista', 'Rejeitado', 'Contratado'])
        
        submit_button = st.form_submit_button(label='Adicionar Vaga')
        if submit_button:
            if not (id_vaga and data_candidatura and vaga and nome_empresa and link_vaga and origem_candidatura and pessoas_adicionadas and linkedin_mensagem and ultimo_contato):
                st.warning('Por favor, preencha todos os campos.')
            else:
                try:
                    data_candidatura = datetime.strptime(str(data_candidatura), '%Y-%m-%d')
                    new_data = pd.DataFrame({
                        'ID': [id_vaga],
                        'Data da Candidatura': [data_candidatura],
                        'Vaga': [vaga],
                        'Nome da Empresa': [nome_empresa],
                        'Link da vaga': [link_vaga],
                        'Origem da Candidatura': [origem_candidatura],
                        'Pessoas da empresa adicionadas': [pessoas_adicionadas],
                        'Linkedin da pessoa que mandei a mensagem': [linkedin_mensagem],
                        'Ultimo contato pelo linkedin': [ultimo_contato],
                        'Status': [status]
                    })
                    
                    df = pd.concat([df, new_data], ignore_index=True)
                    save_data(df, user_id)
                    st.success('Vaga adicionada com sucesso!')
                except ValueError:
                    st.error('Erro ao converter a data. Verifique o formato da data inserida.')

    st.subheader('Visualizar Vagas')
    if st.button('Mostrar Vagas'):
        st.write(df)

    st.subheader('Treinar Modelo')
    if st.button('Treinar Modelo'):
        model, scaler, X_columns = train_model(df)
        if model:
            st.success('Modelo treinado com sucesso!')
        else:
            st.error('Erro ao treinar o modelo. Adicione mais dados e tente novamente.')

    st.subheader('Previsão')
    if st.button('Fazer Previsão'):
        model, scaler, X_columns = train_model(df)
        if model:
            predict(model, scaler, X_columns)
        else:
            st.error('Modelo não treinado. Treine o modelo antes de fazer previsões.')

if __name__ == "__main__":
    run()
