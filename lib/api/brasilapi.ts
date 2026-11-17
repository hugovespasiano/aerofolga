/**
 * Conector oficial com a BrasilAPI para obtenção de feriados nacionais e estaduais do Brasil.
 * 100% Gratuito, aberto e sem necessidade de tokens de autenticação.
 * Documentação: https://brasilapi.com.br/docs#tag/Feriados-Nacionais
 */

export interface BrasilApiHoliday {
  date: string; // Formato AAAA-MM-DD
  name: string;
  type: 'national' | 'state';
}

export async function fetchNationalHolidays(year: number = new Date().getFullYear()): Promise<BrasilApiHoliday[]> {
  try {
    const response = await fetch(`https://brasilapi.com.br/api/feriados/v1/${year}`, {
      next: { revalidate: 86400 }, // Cache de 24 horas (Boring Tech)
    });

    if (!response.ok) {
      throw new Error(`Falha ao consultar BrasilAPI: ${response.statusText}`);
    }

    const data: BrasilApiHoliday[] = await response.json();
    return data;
  } catch (error) {
    console.error(`[BrasilAPI] Erro ao buscar feriados para o ano ${year}:`, error);
    // Retorno de fallback estático essencial caso a rede falhe
    return [
      { date: `${year}-01-01`, name: 'Confraternização Universal', type: 'national' },
      { date: `${year}-04-21`, name: 'Tiradentes', type: 'national' },
      { date: `${year}-05-01`, name: 'Dia do Trabalho', type: 'national' },
      { date: `${year}-09-07`, name: 'Independência do Brasil', type: 'national' },
      { date: `${year}-10-12`, name: 'Nossa Senhora Aparecida', type: 'national' },
      { date: `${year}-11-02`, name: 'Finados', type: 'national' },
      { date: `${year}-11-15`, name: 'Proclamação da República', type: 'national' },
      { date: `${year}-11-20`, name: 'Dia da Consciência Negra', type: 'national' },
      { date: `${year}-12-25`, name: 'Natal', type: 'national' },
    ];
  }
}
