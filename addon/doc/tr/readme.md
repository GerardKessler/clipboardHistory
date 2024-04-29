# Pano Geçmişi

[gera Kessler](http://gera.ar)

ve Héctor Benítez'in paha biçilmez işbirliğiyle.

Bu eklenti, bir pano geçmişini yerel bir veritabanında tutarak yönetmenizi sağlar; bu, sistem yeniden başlatıldığında bile metinleri korumanıza olanak tanır.
Geçmişe göz atma, arama, sayma, favoriler, yedekleme ve öğe görüntüleme işlevleri için komutlar ekler.A parte de la interacción a través de la capa de comandos con funciones gelişmiş, derleme istemeyenler için basit bir grafik versiyonunu kullanabilirsiniz.

NVDA'yı ilk kez kurup başlattığınızda, veritabanını içeren "clipboard_history" dosyası oluşturulur. Bu dosya, kullanıcı yapılandırma dizinlerindeki nvda klasörünün kökünde bulunur.
Pano değişikliklerini yakalamak ve yeni metin içeriği olduğunda veritabanını güncellemek için bir dinleyici de oluşturulur.El historial no guarda duplicaciones para evitar un Gereksiz veritabanı büyümesi. Mevcut bir metni kopyalarken listedeki ilk konuma kopyalanır ve önceki metin elenir.

Girdi hareketleri iletişim kutusunda, Pano Geçmişi kategorisinde atanabilir 2 işlev vardır. Yani:

* Komut katmanını etkinleştirir
* Grafik arayüzü etkinleştirir

Önemli Not:  
Pano geçmişi hassas verileri tutabilir; bu nedenle, ayarların bir kopyasıyla taşınabilir bir sürümü paylaşmadan önce içeriği silmek kullanıcının sorumluluğundadır.

## Komut katmanı

Komut katmanını önceden atanmış hareketle etkinleştirdiğimizde aşağıdaki kısayol gruplarına sahip oluruz. Aşağıda listelenen tuşlar dışında herhangi bir tuşa basıldığında komut katmanı devre dışı bırakılır ve tuşlar varsayılan işlevlerine geri döner.

### Hareket Listesi:

* Yukarı ok; önceki liste öğesi
* Aşağı ok; Sonraki liste öğesi
* Baş; listedeki ilk öğe
* son; listedeki son öğe

### Listedeki odaklanılan öğeyi etkileyen özellikler

* Geri Silme tuşu; genel listedeki öğeyi kaldırır. Favorilerdeyse bu şekilde favorilerden kaldırır.
* Sağ ok; metni panoya kopyalar ve genel listenin başına taşır
* Sol ok; metni daha sonra incelenmek üzere bir NVDA penceresinde açar
* v; Metni odaklanılan pencereye yapıştırır.
* c; boşluklar, boşluklar, kelimeler ve satırlar hariç karakter sayısını sözlü olarak ifade eder
* f; öğeyi favori olarak işaretler veya işaretini kaldırır.

### Arama işlevleri

* b; listedeki öğeleri aramak için pencereyi etkinleştirir
* f3; aranan metnin bir sonraki eşleşmesine ilerler
* g; öğeye sipariş numarasına göre odaklanmak için pencereyi etkinleştirir

### Diğer özellikler

* f1; komut katmanı kısayollarının listesini içeren bir NVDA penceresi görüntüler
* tab; genel liste ile favoriler listesi arasında geçiş yapar.
* e; favori olup olmadığını, geçerli öğenin dizin numarasını ve listedeki toplam sayıyı sözlü olarak belirtir
* s; eklenti ayarları iletişim kutusunu gösterir
* z; liste öğesi silme iletişim kutusunu gösterir
* escape; komut katmanını devre dışı bırakır.

## Öğeleri ara

Geçmişteki bir metni kelimelere göre aramak için, komut katmanı etkinken b harfine basmanız yeterlidir.  
Bu, herhangi bir kelimeyi veya ifadeyi yazıp enter tuşuna bastığınızda aramanın gerçekleştirileceği arama diyalog penceresini açar.  
Sonuç bulunursa metin ve sıra numarası sözlü olarak ifade edilir. F3 tuşuna basarsak aynı içerikle tekrar arama yapılır, başka bir eşleşme bulunursa bir sonraki sonuca geçilir.

## Favoriler

Sekme tuşu, odağı genel liste ile Favoriler listesi arasında değiştirir. İkincisi aktif olduğunda geri silme tuşu, öğenin favori durumunu kaldırır ve listeden çıkarır.
Genel listede, f harfi favori durumunu değiştirir ve onu favoriler listesine ekler veya listeden çıkarır.  
Kopyalama, görüntüleme, arama, yapıştırma, konuşma sırası ve pencereyi kapatma işlevleri her iki listede de aynı işlevi yerine getirir.

## Ayarlar penceresi

Komut katmanı etkinken s harfine veya grafik versiyonda control + p'ye basmak, Ayarlar arayüzünü görüntüler.  
İçinde aşağıdakiler değiştirilebilir:

### Kaydedilecek dize sayısı

Burada veritabanına kaç öğenin kaydedileceğini belirleyebilirsiniz. Bu sayı aşıldığında son girişten önceki eski girişler silinir.  
Maksimum sayıda öğeyi yapılandırırken veritabanı bu değerden daha büyük bir miktar içeriyorsa, yeni veri girildiğinde eski girişler silinecek ancak mevcut öğe sayısı korunacak, böylece kullanıcı hangilerini sileceğini seçebilecektir.

### Sesler

Eklenti seslerini açma veya kapatma

### Dizin öğe sayısı

Bu kutu etkinleştirilirse, öğe listesine göz atıldığında sıra numarası söylenir.

### Veritabanını dışa aktar

Bu düğme, içinde depolanan verileri yedeklemek için veritabanını mevcut durumunda kaydetme iletişim kutusunu etkinleştirir ve bu eklentiyle daha sonra başka bir NVDA'dan içe aktarmaya olanak tanır.

### Veritabanını içe aktar

Bu seçenek, geçerli veritabanında bulunmayan öğeleri kurtarmak amacıyla önceden dışa aktarılan veritabanında arama yapmak için bir iletişim kutusunu etkinleştirir.

## Grafik arayüz

Hareket atandıktan sonra bu seçenek, gezinmeyi ve geçmişle etkileşimi kolaylaştıran grafik arayüzü açar.  
Saklanan farklı öğeler, yukarı ve aşağı oklarla kaydırılabilen bir liste biçiminde görünür.  
Seçilen listedeki bir öğe üzerindeyken sekme tuşuna basılırsa, öğe içeriği salt okunur bir kutuda görüntülenir.  
Öğe listesinde aşağıdaki kısayollar mevcuttur:

* f1; öğelerin konumunu ve toplamını sözlü olarak ifade eder
* Enter; odaklanılan öğenin metnini panoya kopyalar
* f5; liste içeriğini yeniler
* Sil tuşu; odaklanılan öğeyi kaldırır.
* alt + sil; geçmişi siler.
* CTRL + p; eklenti Ayarları penceresini etkinleştirir
* escape; arayüzü kapatır.
