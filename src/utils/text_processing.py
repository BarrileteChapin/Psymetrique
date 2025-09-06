"""
Text processing utilities for PsyQuant application
"""

import re
from typing import List


def extract_meaningful_words(text: str) -> List[str]:
    """Extract meaningful words from text, filtering out common stop words, short words, and entity replacement tokens"""
    # Multilingual stop words (English, Spanish, French, Portuguese)
    stop_words = {
        # English
        'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by',
        'i', 'you', 'he', 'she', 'it', 'we', 'they', 'me', 'him', 'her', 'us', 'them',
        'my', 'your', 'his', 'her', 'its', 'our', 'their', 'mine', 'yours', 'hers', 'ours', 'theirs',
        'am', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did',
        'will', 'would', 'could', 'should', 'may', 'might', 'must', 'can', 'shall',
        'this', 'that', 'these', 'those', 'here', 'there', 'where', 'when', 'why', 'how',
        'what', 'which', 'who', 'whom', 'whose', 'all', 'any', 'some', 'no', 'not', 'only', 'own', 'same',
        'so', 'than', 'too', 'very', 'just', 'now', 'then', 'once', 'also', 'still', 'back', 'even',
        'well', 'way', 'much', 'many', 'most', 'more', 'less', 'few', 'little', 'large', 'small',
        'good', 'bad', 'new', 'old', 'first', 'last', 'long', 'short', 'high', 'low', 'right', 'left',
        'big', 'small', 'up', 'down', 'out', 'off', 'over', 'under', 'again', 'further', 'then', 'once',
        
        # Spanish
        'el', 'la', 'de', 'que', 'y', 'a', 'en', 'un', 'para', 'é', 'com', 'não', 'te', 'lo', 'le', 'da', 'su',
        'por', 'son', 'con', 'para', 'al', 'una', 'del', 'los', 'las', 'pero', 'como', 'me', 'si', 'ya',
        'todo', 'esta', 'muy', 'más', 'bien', 'puede', 'ser', 'tiene', 'hace', 'cuando', 'donde', 'quien',
        'porque', 'sobre', 'entre', 'hasta', 'desde', 'sin', 'bajo', 'tras', 'durante', 'ante', 'contra',
        'hacia', 'según', 'mediante', 'salvo', 'excepto', 'incluso', 'además', 'también', 'tampoco',
        'ni', 'o', 'u', 'sino', 'aunque', 'mientras', 'como', 'cuanto',
        'yo', 'tú', 'él', 'ella', 'nosotros', 'vosotros', 'ellos', 'ellas', 'mi', 'tu', 'nuestro', 'vuestro',
        'este', 'esta', 'estos', 'estas', 'ese', 'esa', 'esos', 'esas', 'aquel', 'aquella', 'aquellos', 'aquellas',
        
        # French
        'le', 'de', 'et', 'à', 'un', 'il', 'être', 'en', 'avoir', 'que', 'pour', 'dans', 'ce', 'son',
        'une', 'sur', 'avec', 'ne', 'se', 'pas', 'tout', 'plus', 'par', 'grand', 'du', 'me', 'te', 'nous',
        'vous', 'ils', 'elles', 'mon', 'ton', 'sa', 'notre', 'votre', 'leur', 'leurs', 'mes', 'tes', 'ses',
        'nos', 'vos', 'cette', 'ces', 'celui', 'celle', 'ceux', 'celles', 'qui', 'quoi', 'dont', 'où',
        'comment', 'pourquoi', 'quand', 'combien', 'quel', 'quelle', 'quels', 'quelles', 'lequel', 'laquelle',
        'lesquels', 'lesquelles', 'auquel', 'auxquels', 'auxquelles', 'duquel', 'desquels', 'desquelles',
        'mais', 'ou', 'donc', 'or', 'ni', 'car', 'si', 'comme', 'bien', 'très',
        'aussi', 'encore', 'déjà', 'toujours', 'jamais', 'souvent', 'parfois', 'quelquefois', 'maintenant',
        'hier', 'demain', 'ici', 'là', 'partout',
        
        # Portuguese
        'o', 'a', 'de', 'e', 'do', 'da', 'em', 'um', 'para', 'é', 'com', 'não', 'uma', 'os', 'no', 'se',
        'na', 'por', 'mais', 'as', 'dos', 'como', 'mas', 'foi', 'ao', 'ele', 'das', 'tem', 'à', 'seu',
        'sua', 'ou', 'ser', 'quando', 'muito', 'há', 'nos', 'já', 'está', 'eu', 'também', 'só', 'pelo',
        'pela', 'até', 'isso', 'ela', 'entre', 'era', 'depois', 'sem', 'mesmo', 'aos', 'ter', 'seus',
        'suas', 'numa', 'pelos', 'pelas', 'esse', 'essa', 'esses', 'essas', 'aquele', 'aquela', 'aqueles',
        'aquelas', 'este', 'esta', 'estes', 'estas', 'isto', 'nisso', 'nisto', 'disso', 'disto', 'desse',
        'dessa', 'desses', 'dessas', 'nesse', 'nessa', 'nesses', 'nessas', 'naquele', 'naquela', 'naqueles',
        'naquelas', 'daquele', 'daquela', 'daqueles', 'daquelas', 'lhe', 'lhes',
        'meu', 'minha', 'meus', 'minhas', 'teu', 'tua', 'teus', 'tuas', 'nosso', 'nossa', 'nossos', 'nossas',
        'vosso', 'vossa', 'vossos', 'vossas', 'dele', 'dela', 'deles', 'delas', 'quem', 'qual',
        'quais', 'quanto', 'quanta', 'quantos', 'quantas', 'onde', 'porque', 'porquê',
        'caso', 'embora', 'ainda', 'contudo', 'entretanto', 'todavia', 'porém',
        'senão', 'aliás', 'então', 'portanto', 'logo', 'pois', 'assim', 'bem', 'mal', 'melhor',
        'pior', 'menos', 'pouco', 'bastante', 'demais', 'tão', 'tal', 'tanto', 'tanta', 'tantos',
        'tantas', 'todo', 'toda', 'todos', 'todas', 'outro', 'outra', 'outros', 'outras', 'qualquer',
        'quaisquer', 'algum', 'alguma', 'alguns', 'algumas', 'nenhum', 'nenhuma', 'nenhuns', 'nenhumas',
        'certo', 'certa', 'certos', 'certas', 'vário', 'vária', 'vários', 'várias', 'diverso', 'diversa',
        'diversos', 'diversas'
    }

    text = text.lower()

    text = re.sub(r'(?i)\[[a-z_]+\]', '', text)

    text = re.sub(r'\*+', '', text)
    text = re.sub(r'\bx{2,}\b', '', text, flags=re.IGNORECASE)
    text = re.sub(r'_{2,}', '', text)
    text = re.sub(r'#{2,}', '', text)
    text = re.sub(r'-{2,}', '', text)
    text = re.sub(r'\.{2,}', '', text)
    text = re.sub(r'\b\[?redacted\]?\b', '', text)
    text = re.sub(r'\b\[?removed\]?\b', '', text)
    text = re.sub(r'\b\[?anonymized\]?\b', '', text)
    text = re.sub(r'\b\[?masked\]?\b', '', text)
    text = re.sub(r'\b\[?hidden\]?\b', '', text)

    words = re.findall(r'\b[a-zA-ZáéíóúàèìòùâêîôûãõçñüÁÉÍÓÚÀÈÌÒÙÂÊÎÔÛÃÕÇÑÜ]+\b', text)

    meaningful_words = []
    for word in words:
        if len(word) <= 2:
            continue
        if not word.isalpha():
            continue
        if word.lower() in stop_words:
            continue
        if re.match(r'^[x*_#-]+$', word, re.IGNORECASE):
            continue
        meaningful_words.append(word.lower())

    return meaningful_words
