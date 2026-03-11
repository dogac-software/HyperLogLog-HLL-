import hashlib
import math

class HyperLogLog:
    def __init__(self, p=10):
        """
        p: Kova (bucket) sayısını belirleyen bit sayısı.
        m = 2^p kova oluşturulur.
        """
        if not (4 <= p <= 16):
            raise ValueError("p değeri 4 ile 16 arasında olmalıdır.")
        
        self.p = p
        self.m = 1 << p  # 2^p
        self.registers = [0] * self.m
        
        # Alfa (Düzeltme Faktörü) hesaplaması
        if self.m == 16:
            self.alpha = 0.673
        elif self.m == 32:
            self.alpha = 0.697
        elif self.m == 64:
            self.alpha = 0.709
        else:
            self.alpha = 0.7213 / (1.0 + 1.079 / self.m)

    def _hash(self, item):
        """
        SHA-256 kullanarak yüksek kaliteli bir 64-bit hash üretir.
        """
        hash_hex = hashlib.sha256(str(item).encode('utf8')).hexdigest()
        return int(hash_hex[:16], 16) # İlk 64 bitini (16 hex karakter) alıyoruz

    def _get_rho(self, w, max_width):
        """
        Geriye kalan bitlerdeki ilk '1'in pozisyonunu (ardışık sıfır sayısı + 1) bulur.
        """
        rho = 1
        while (w & 1) == 0 and rho <= max_width:
            rho += 1
            w >>= 1
        return rho

    def add(self, item):
        """
        Elemanı HLL yapısına ekler.
        """
        x = self._hash(item)
        
        # İlk p biti kova indeksi (j) olarak kullan
        j = x & (self.m - 1)
        
        # Geri kalan bitleri al
        w = x >> self.p
        
        # İlk 1'in pozisyonunu bul ve register'ı güncelle
        self.registers[j] = max(self.registers[j], self._get_rho(w, 64 - self.p))

    def count(self):
        """
        Harmonik ortalama ve düzeltme faktörlerini kullanarak tahmini sayıyı hesaplar.
        """
        Z = sum(math.pow(2.0, -x) for x in self.registers)
        E = self.alpha * (self.m ** 2) / Z

        # Küçük Veri Seti Düzeltmesi (Linear Counting)
        if E <= (5.0 / 2.0) * self.m:
            V = self.registers.count(0)
            if V > 0:
                E = self.m * math.log(self.m / float(V))
                
        # Büyük Veri Seti Düzeltmesi
        elif E > (1 / 30.0) * (1 << 32):
            E = -(1 << 32) * math.log(1.0 - (E / (1 << 32)))

        return int(E)

    def merge(self, other_hll):
        """
        İki HLL yapısını veri kaybı olmadan birleştirir.
        """
        if self.p != other_hll.p:
            raise ValueError("Birleştirilecek HLL yapıları aynı p değerine sahip olmalıdır.")
        
        merged_hll = HyperLogLog(self.p)
        merged_hll.registers = [max(r1, r2) for r1, r2 in zip(self.registers, other_hll.registers)]
        return merged_hll

# ==========================================
# TEST VE KULLANIM ÖRNEĞİ
# ==========================================
if __name__ == "__main__":
    # 1. Tekil HLL Testi
    hll = HyperLogLog(p=10) # m = 1024 kova
    gercek_sayi = 100000
    
    print(f"[{gercek_sayi} benzersiz eleman ekleniyor...]")
    for i in range(gercek_sayi):
        hll.add(f"veri_satiri_{i}")
        
    tahmin = hll.count()
    hata_orani = abs(gercek_sayi - tahmin) / gercek_sayi * 100
    
    print(f"Gerçek Sayı: {gercek_sayi}")
    print(f"HLL Tahmini: {tahmin}")
    print(f"Hata Oranı: %{hata_orani:.2f}")
    print("-" * 30)
    
    # 2. Birleştirme (Merge) Testi
    hll1 = HyperLogLog(p=10)
    hll2 = HyperLogLog(p=10)
    
    # hll1'e 1'den 50.000'e kadar ekle
    for i in range(50000):
        hll1.add(f"ortak_kullanici_{i}")
        
    # hll2'ye 25.000'den 75.000'e kadar ekle (25.000'i kesişiyor)
    for i in range(25000, 75000):
        hll2.add(f"ortak_kullanici_{i}")
        
    merged = hll1.merge(hll2)
    print("Birleştirilmiş HLL (Beklenen Eşsiz: 75000)")
    print(f"HLL1 Tahmin: {hll1.count()}")
    print(f"HLL2 Tahmin: {hll2.count()}")
    print(f"Merge Tahmin: {merged.count()}")
