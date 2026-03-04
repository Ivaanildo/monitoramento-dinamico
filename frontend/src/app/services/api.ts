export const api = {
    get: async (url: string) => {
        const res = await fetch(url, {
            credentials: "include",
        });
        if (!res.ok) {
            if (res.status === 401) throw new Error("Unauthorized");
            throw new Error("HTTP " + res.status);
        }
        return res.json();
    },

    getConsulta: async (rota_id: string) => {
        const res = await fetch(`/rotas/${rota_id}/consultar`, {
            credentials: "include",
        });
        if (!res.ok) {
            if (res.status === 401) throw new Error("Unauthorized");
            throw new Error("HTTP " + res.status);
        }
        return res.json();
    },
}
