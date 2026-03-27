# telegram-cli — Kullanıcı Kılavuzu

Bu kılavuz, **telegram-cli**'nin nasıl kurulacağını ve kullanılacağını açıklamaktadır. telegram-cli, resmi uygulama olmadan Telegram mesajlarınızı yedeklemenizi, okumanızı ve yönetmenizi sağlayan bir komut satırı aracıdır. Programcı olmanıza gerek yoktur. Sadece adımları sırayla takip edin.

---

Telegram, düzinelerce dil ve ülkede 900 milyonun üzerinde aylık aktif kullanıcısıyla dünyanın en yaygın kullanılan mesajlaşma uygulamalarından biridir.

| Dil | ISO 639‑1 | Başlıca Ülkeler | Tahmini Telegram Kullanıcısı |
|-----|-----------|-----------------|------------------------------|
| Rusça | ru | Rusya, Ukrayna, Beyaz Rusya | ≈ 120–150 milyon |
| İngilizce | en | Hindistan, ABD, İngiltere | ≈ 110–130 milyon |
| Farsça | fa | İran, Afganistan, Tacikistan | ≈ 40–50 milyon |
| Türkçe | tr | Türkiye, Kıbrıs, Almanya (diaspora) | ≈ 25–35 milyon |
| Arapça | ar | Mısır, Irak, Suudi Arabistan | ≈ 20–30 milyon |
| Almanca | de | Almanya, Avusturya, İsviçre | ≈ 8–12 milyon |

Telegram, bazı ülkelerde veya coğrafi bölgelerde zaman zaman erişilemez ya da engellenmiş olabilir. Bu durumlarda telegram-cli yardımcı olabilir — resmi uygulamalardan bağımsız olarak Telegram verilerinizle komut satırından çalışmanızı sağlar.

Özellikle Telegram içeriğinin **çevrimdışı işlenmesi** için kullanışlıdır; örneğin konuşmaları, grupları ve kanalları daha sonra yapay zeka araçları veya diğer otomasyon sistemleriyle analiz etmek üzere yedeklemek gibi.

Bu aracı kullanmak için programcı olmanıza gerek yoktur. Sadece aşağıdaki adımları takip edin.

---

## İçindekiler

- [Başlarken — Windows Hızlı Başlangıç](#başlarken--windows-hızlı-başlangıç)
- [Genel Bakış — telegram-cli Ne Yapabilir?](#genel-bakış--telegram-cli-ne-yapabilir)
- [Kurulum Kontrol Listesi](#kurulum-kontrol-listesi)
- [Nasıl Kurulur](#nasıl-kurulur)
- [Güvenlik — Kimlik Bilgilerinizi Koruyun](#güvenlik--kimlik-bilgilerinizi-koruyun)
- [Dosyalarınız Nereye Kaydedilir](#dosyalarınız-nereye-kaydedilir)
- [Komut Referansı](#komut-referansı)
- [Hata İşleme](#hata-işleme)
- [Gelişmiş](#gelişmiş)
- [Sorun Giderme](#sorun-giderme)

---

## Başlarken — Windows Hızlı Başlangıç

> Bu bölüm, `telegram-cli.exe` indiren **Windows kullanıcıları** içindir. macOS kullanıyorsanız veya Python sürümünü tercih ediyorsanız, [Kurulum Kontrol Listesi](#kurulum-kontrol-listesi) bölümüne atlayın.

Sıfırdan ilk yedeğinize ulaşmak için gereken beş komut aşağıdadır. Her komut bu kılavuzun ilerleyen bölümlerinde ayrıntılı olarak açıklanmaktadır.

**Başlamadan önce:** `telegram-cli.exe` dosyasını ve bu kullanıcı kılavuzunu [Nasıl Kurulur](#nasıl-kurulur) bölümünde açıklandığı gibi indirin. Ardından `telegram-cli.exe` dosyasını istediğiniz bir klasöre koyun — örneğin `C:\Users\AdınızSoyadınız\telegram-cli\`. Komut İstemi'ni o klasörde açın (bkz. [Komut İstemi nasıl açılır](#komut-istemi-nasıl-açılır-windows-veya-terminal-macos) aşağıda).

**Adım 1 — API kimlik bilgilerinizi alın:** <https://my.telegram.org/apps> adresinden (tek seferlik işlem, ayrıntılar için bkz. [Adım 2](#adım-2--bir-telegram-uygulaması-oluşturun)).

**Adım 2 — Oturum açın:**
```
telegram-cli init
```
İstendiğinde `api_id`, `api_hash` ve telefon numaranızı girin. Telegram uygulamanıza gönderilen giriş kodunu yazın.

**Adım 3 — Doğrulayın:**
```
telegram-cli whoami
```
Adınızı ve telefon numaranızı görmeniz gerekir.

**Adım 4 — Konuşmalarınızı listeleyin:**
```
telegram-cli get-dialogs
```
Yedeklemek istediğiniz konuşmanın kimliğini bulun (`ID` sütunundaki numara).

**Adım 5 — Yedekleyin:**
```
telegram-cli backup -1001234567890 --limit=500
```
`-1001234567890` yerine Adım 4'teki gerçek kimliği yazın. Mesajlarınız, geçerli dizinde `synchromessotron\` klasörüne kaydedilir.

> **İlk çalıştırmada SmartScreen uyarısı:** Windows _"Windows bilgisayarınızı korudu"_ mesajı gösterebilir. **Daha fazla bilgi** → **Yine de çalıştır**'a tıklayın. Bu yalnızca bir kez gerçekleşir.

---

## Genel Bakış — telegram-cli Ne Yapabilir?

| Komut | Ne Yapar |
|-------|----------|
| `init` | Kimlik bilgilerini ve oturumu ayarlar |
| `whoami` | Oturumu doğrular ve kullanıcı bilgilerini gösterir |
| `ping` | Telegram'ın erişilebilirliğini kontrol eder |
| `get-dialogs` | Konuşmalarınızı listeler |
| `backup` | Tam veya artımlı mesaj yedeklemesi |
| `send` | Bir konuşmaya mesaj gönderir |
| `edit` | Daha önce gönderilmiş bir mesajı düzenler |
| `delete` | Kendi mesajlarınızı siler |
| `download-media` | Bir mesajdaki fotoğraf, video veya dosyayı indirir |
| `help` | Yardımı kendi dilinizde gösterir |
| `version` | Sürüm bilgilerini gösterir |

> **"Dialog" nedir?** Telegram'da "dialog" kelimesi her türlü konuşmayı ifade eder — bir kişiyle özel sohbet, grup sohbeti veya kanal.

---

## Kurulum Kontrol Listesi

telegram-cli'yi kullanmak için aşağıdaki dört adımı bir kez tamamlamanız gerekir:

- [ ] **Adım 1** — Platformunuz için dosyayı indirin.
- [ ] **Adım 2** — API kimlik bilgilerinizi almak için bir Telegram uygulaması oluşturun.
- [ ] **Adım 3** — Oturumunuzu ayarlayın — telegram-cli sizi sisteme dahil eder.
- [ ] **Adım 4** — Kurulumun çalıştığını doğrulayın.

Aşağıdaki bölümler her adımı ayrıntılı olarak açıklamaktadır.

---

## Nasıl Kurulur

### Adım 1 — Sürümünüzü seçin ve indirin

[Releases](https://github.com/vsirotin/synchromessotron/releases/) sayfasına gidin, en son kararlı sürümü bulun, "Assets" bölümünü açın ve platformunuz için uygun dosyayı indirin:

| Platform | Dosya | Ek yazılım gerekli mi? |
|----------|-------|------------------------|
| **Windows** | `telegram-cli.exe` | Hayır |
| **macOS** | `telegram-cli-macos.zip` | Hayır |
| **Her platform (Python)** | `telegram-cli.pyz` | Evet — Python ≥ 3.11 |

İndirilen dosyayı istediğiniz bir klasöre koyun — örneğin Masaüstünüzdeki veya ana dizininizdeki bir `telegram-cli` klasörüne.

> **Hangi sürümü seçmeliyim?**
>
> - **Windows veya macOS** — platforma özgü dosyayı kullanın. Ek yazılıma gerek yoktur.
> - **Python sürümü** — çalıştırmadan önce kodu incelemek istiyorsanız bu seçeneği tercih edin: `.pyz`, açıp okuyabileceğiniz standart bir Python zip arşividir. Ayrıca Linux'ta da çalışır.

**Platforma özgü ilk çalıştırma notları:**

- **Windows:** Dosyayı ilk çalıştırdığınızda SmartScreen _"Windows bilgisayarınızı korudu"_ mesajı gösterebilir. **Daha fazla bilgi** → **Yine de çalıştır**'a tıklayın. Bu yalnızca bir kez gerçekleşir.
- **macOS:** Zip dosyasını açtıktan sonra Terminal'i o klasörde açın ve şu iki komutu bir kez çalıştırın:
  ```
  chmod +x telegram-cli
  xattr -d com.apple.quarantine telegram-cli
  ```
  Bu komutlar macOS indirme karantinasını kaldırır ve dosyayı çalıştırılabilir hale getirir.
- **Python sürümü:** Python 3.11 veya daha yeni bir sürüm gerektirir. `python3 --version` komutuyla kontrol edin. Gerekirse Python'u <https://www.python.org/downloads/> adresinden yükleyin.

### Adım 2 — Bir Telegram uygulaması oluşturun

telegram-cli'yi kullanmak için kendi Telegram API kimlik bilgilerinize ihtiyacınız vardır. Bu bir kerelik bir işlemdir — bir daha tekrarlamanız gerekmez.

1. Tarayıcıda <https://my.telegram.org/apps> adresini açın ve Telegram telefon numaranızla oturum açın.
2. **API development tools** seçeneğine tıklayın.
3. **Create new application** formunu doldurun. Uygulama başlığı ve kısa adı istediğiniz herhangi bir şey olabilir, örneğin `synchromessotron` / `syncbot`. Platform alanını `Other` olarak bırakabilirsiniz.

   ![Yeni uygulama oluştur iletişim kutusu](../docs/images/telegram1.png)

4. **Create application** düğmesine tıklayın.
5. **App api_id** (kısa bir sayı) ve **App api_hash** (harf ve rakamlardan oluşan uzun bir dize) bilgilerinizi göreceksiniz. Bir sonraki adımda her iki değere de ihtiyacınız olacağından bu tarayıcı sekmesini açık tutun.

   ![api_id ve api_hash](../docs/images/telegram2.png)

### Komut İstemi Nasıl Açılır (Windows veya Terminal macOS)

telegram-cli dosyasını kaydettiğiniz klasörde bir Komut İstemi (Windows) veya Terminal (macOS) penceresi açmanız gerekecektir.

> **Windows — Komut İstemi'ni klasörünüzde açın:**
>
> 1. **Dosya Gezgini**'ni açın ve `telegram-cli.exe` dosyasını kaydettiğiniz klasöre gidin.
> 2. Üst kısımdaki adres çubuğuna tıklayın (klasör yolunu gösterir).
> 3. `cmd` yazın ve **Enter**'a basın. Siyah bir Komut İstemi penceresi açılır ve zaten o klasörde olur.

> **macOS — Terminal'i klasörünüzde açın:**
>
> 1. **Finder**'ı açın ve `telegram-cli` dosyasını kaydettiğiniz klasöre gidin.
> 2. Klasörü sağ tıklayın (veya Control tuşuna basarak tıklayın).
> 3. **New Terminal at Folder** seçeneğini tıklayın. O klasörde bir Terminal penceresi açılır.
>
> (Bu seçeneği görmüyorsanız: **Sistem Ayarları → Gizlilik ve Güvenlik → Uzantılar → Finder Uzantıları** bölümüne gidin ve **New Terminal at Folder** seçeneğini etkinleştirin.)

### Adım 3 — Oturumunuzu ayarlayın

Dosyayı kaydettiğiniz klasörde Komut İstemi (Windows) veya Terminal (macOS) açın (yukarıya bakın) ve şunu çalıştırın:

| Platform | Komut |
|----------|-------|
| **Windows** | `telegram-cli init` |
| **macOS** | `./telegram-cli init` |
| **Python** | `python3 telegram-cli.pyz init` |

Komut şunları yapacaktır:
1. **api_id**, **api_hash** ve **telefon numaranızı** sorar (Adım 2'den).
2. Telegram uygulamanıza bir giriş kodu gönderir — istendiğinde kodu yazın.
3. İki Adımlı Doğrulamayı etkinleştirdiyseniz **2FA parolanızı** sorar.
4. Kimlik bilgilerinizi ve oturumunuzu içeren bir `config.yaml` dosyası oluşturur.

> **2FA parolası nedir?** Telegram'da İki Adımlı Doğrulamayı açtığınızda *kendinizin belirlediği* bir paroladır. Kontrol etmek veya değiştirmek için: Telegram'ı açın → **Ayarlar → Gizlilik ve Güvenlik → İki Adımlı Doğrulama**.

**Beklenen sonuç:**

```
✓ Session created and saved to config.yaml
  Run 'telegram-cli whoami' to verify.
```

### Adım 4 — Kurulumu doğrulayın

| Platform | Komut |
|----------|-------|
| **Windows** | `telegram-cli whoami` |
| **macOS** | `./telegram-cli whoami` |
| **Python** | `python3 telegram-cli.pyz whoami` |

**Beklenen sonuç:**

```
✓ Session valid
  User ID:   123456789
  Name:      Your Name
  Username:  @yourhandle
  Phone:     +1234567890
```

Bunun yerine bir hata görürseniz aşağıdaki [Hata İşleme](#hata-işleme) bölümüne bakın.

Telegram'ın erişilebilir olduğunu da doğrulayın:

| Platform | Komut |
|----------|-------|
| **Windows** | `telegram-cli ping` |
| **macOS** | `./telegram-cli ping` |
| **Python** | `python3 telegram-cli.pyz ping` |

**Beklenen sonuç:**

```
✓ Telegram is reachable (42.3 ms)
```

---

## Güvenlik — Kimlik Bilgilerinizi Koruyun

telegram-cli'nin oluşturduğu `config.yaml` dosyası, Telegram API kimlik bilgilerinizi ve giriş oturumunuzu içerir. **Bu dosyaya sahip olan herkes Telegram hesabınıza erişebilir.**

**Kurallar:**

1. **`config.yaml` dosyasını asla kimseyle paylaşmayın.** Bir parola gibi işlem yapın.
2. **İnternete asla yüklemeyin** — GitHub, Google Drive, Dropbox, e-posta veya paylaşılan herhangi bir konuma koymayın.
3. **Yalnızca kendi bilgisayarınızda** telegram-cli dosyasıyla aynı klasörde saklayın.
4. **Birinin `config.yaml` dosyanızı gördüğünü düşünüyorsanız** — Telegram'da oturumu hemen iptal edin: **Ayarlar → Cihazlar** (veya **Ayarlar → Gizlilik ve Güvenlik → Aktif Oturumlar**) bölümüne gidin ve şüpheli oturumu sonlandırın. Ardından yeni bir oturum oluşturmak için `telegram-cli init` komutunu tekrar çalıştırın.

> `config.yaml.example` dosyası gerçek kimlik bilgileri içermeyen bir şablondur — paylaşması güvenlidir.

---

## Dosyalarınız Nereye Kaydedilir

telegram-cli tarafından üretilen tüm veriler (yedekler, indirilen medya dosyaları) bir **çıktı klasörüne** kaydedilir.

### Varsayılan konum

Varsayılan olarak, telegram-cli'yi çalıştırdığınız klasörün içinde `synchromessotron` adlı bir klasör oluşturulur:

```
<geçerli klasör>/synchromessotron/
```

### Farklı bir klasör seçme

`--outdir` parametresiyle farklı bir konum seçebilirsiniz:

| Platform | Örnek |
|----------|-------|
| **Windows** | `telegram-cli backup -1001234567890 --outdir=C:\MyBackups` |
| **macOS** | `./telegram-cli backup -1001234567890 --outdir=/Users/yourname/MyBackups` |
| **Python** | `python3 telegram-cli.pyz backup -1001234567890 --outdir=/path/to/my/data` |

> **Çakışma kuralı:** Hem `--outdir` hem de `config.yaml` içindeki `output_dir` ayarlanmışsa ve farklı yollara işaret ediyorlarsa, komut hata vererek çıkar. Çakışmayı çözmek için birini kaldırın.

telegram-cli, başlamadan önce klasörün yazılabilir olduğunu kontrol eder. Masaüstünüzdeki veya ana dizininizdeki konumların çoğunun zaten yazma izni vardır. "Yazma izni" hatası alırsanız [Sorun Giderme](#sorun-giderme) bölümüne bakın.

### Konuşmalarınızın nasıl düzenlendiği

Her konuşma için şu adlandırma kuralı kullanılarak bir alt klasör oluşturulur:

```
<adın ilk 10 karakteri>_<konuşma kimliği>
```

- Addaki boşluklar alt çizgiyle (`_`) değiştirilir.
- Ad 10 karakterden kısaysa tam ad kullanılır.

| Konuşma | Alt klasör |
|---------|------------|
| `Мемуары кочевого программиста. Байки, были, думы` (Kimlik -718738386) | `Мемуары_ко_718738386` |
| `Telegram` (Kimlik 777000) | `Telegram_777000` |

Her konuşma klasörünün içinde mesajlar yıla göre, mesaj sayısı fazlaysa aya veya güne göre düzenlenir (ayrıntılar için bkz. [Gelişmiş](#gelişmiş)).

### Hangi dosyalar kaydedilir

Her düzeyde iki dosya oluşturulur:

| Dosya | İçerik |
|-------|--------|
| `messages.json` | Tam mesaj verisi (diğer araçlarla kullanım için). |
| `messages.md` | Yazar, tarih ve mesaj metni — herhangi bir metin düzenleyicide okunması kolaydır. |

### Fotoğraf, video ve diğer içeriklerin kaydedilmesi

Varsayılan olarak yalnızca mesajlar kaydedilir. Diğer içerikleri de eklemek için `backup` komutuna bayraklar ekleyin:

| Bayrak | Ne kaydedilir |
|--------|--------------|
| `--media` | Fotoğraflar ve videolar |
| `--files` | Belgeler ve dosya ekleri |
| `--music` | Ses parçaları |
| `--voice` | Sesli mesajlar |
| `--links` | Bağlantı önizlemeleri ve URL'ler |
| `--gifs` | GIF animasyonları |
| `--members` | Konuşma katılımcılarının listesi |

Örnek — mesajları ve fotoğrafları yedekleyin:

| Platform | Komut |
|----------|-------|
| **Windows** | `telegram-cli backup -1001234567890 --media` |
| **macOS** | `./telegram-cli backup -1001234567890 --media` |
| **Python** | `python3 telegram-cli.pyz backup -1001234567890 --media` |

Örnek — her şeyi yedekleyin:

```
telegram-cli backup -1001234567890 --media --files --music --voice --links --gifs --members
```

### Örnek klasör yapısı

`--media --members` parametreleriyle `backup` çalıştırdıktan sonra:

```
synchromessotron/
├── Мемуары_ко_718738386/
│   ├── members/
│   ├── 2025/
│   │   ├── 01/
│   │   │   ├── messages.json
│   │   │   ├── messages.md
│   │   │   └── media/
│   │   └── 02/
│   │       ├── messages.json
│   │       └── messages.md
│   └── 2026/
│       ├── messages.json
│       └── messages.md
└── Telegram_777000/
    └── 2026/
        ├── messages.json
        └── messages.md
```

Bu örnekte:
- "Мемуары кочевого…" konuşmasının 2025 yılında 50'den fazla mesajı vardı, bu nedenle aylık alt klasörlere bölündü. 2026'da daha az mesaj olduğundan bunlar yıl klasöründe bir arada kaldı.
- "Telegram" konuşmasının toplam mesaj sayısı azdı — aylık bölümlemeye gerek duyulmadı.

---

## Komut Referansı

### get-dialogs — Konuşmalarınızı listeleyin

```
get-dialogs [--limit=N] [--outdir=DIR]
```

**Parametreler:**

| Parametre | Varsayılan | Açıklama |
|-----------|------------|----------|
| `--limit` | 100 | Döndürülecek maksimum konuşma sayısı. Daha fazlası için `--limit=500` veya daha yüksek bir değer kullanın. |
| `--outdir` | — | `dialogs.json` dosyasını bu klasöre de kaydedin (bkz. [Dosyalarınız Nereye Kaydedilir](#dosyalarınız-nereye-kaydedilir)). |

**Örnekler:**

| Platform | Komut |
|----------|-------|
| **Windows** | `telegram-cli get-dialogs --limit=50` |
| **macOS** | `./telegram-cli get-dialogs --limit=50` |
| **Python** | `python3 telegram-cli.pyz get-dialogs --limit=50` |

**Beklenen sonuç:**

```
  TYPE         ID                 NAME
  ------------ ------------------ ------------------------------------------
  User         123456789          Your Name  @yourhandle
  Channel      -1001234567890     Family Group  @familygroup
  Chat         -987654321         Old Project

3 dialogs found.
```

`--outdir` kullanıldığında tablo ekrana yine de yazdırılır ve `dialogs.json` çıktı klasörüne de kaydedilir.

Bir sorun oluşursa: `NETWORK_ERROR`, `PERMISSION_DENIED`, `RATE_LIMITED`, `SESSION_INVALID`. Bkz. [Hata İşleme](#hata-işleme).

---

### backup — Mesajları yedekleyin

```
backup <dialog_id> [--since=TIMESTAMP] [--upto=TIMESTAMP] [--limit=N] [--outdir=DIR]
       [--media] [--files] [--music] [--voice] [--links] [--gifs] [--members]
       [--estimate] [--count]
```

**Parametreler:**

| Parametre | Varsayılan | Açıklama |
|-----------|------------|----------|
| `<dialog_id>` | — | Konuşma kimliği (zorunlu). Bulmak için `get-dialogs` kullanın. |
| `--since` | — | Yalnızca bu tarih ve saatten **sonra** gönderilen mesajları indirin (biçim: `2026-01-01T00:00:00+00:00`). |
| `--upto` | — | Yalnızca bu tarih ve saatte veya **öncesinde** gönderilen mesajları indirin. |
| `--limit` | 100 | İndirilecek maksimum mesaj sayısı. |
| `--outdir` | `./synchromessotron` | Dosyaları varsayılan yerine bu klasöre kaydedin. |
| `--media` | kapalı | Fotoğrafları ve videoları da indirin. |
| `--files` | kapalı | Belgeleri ve dosya eklerini de indirin. |
| `--music` | kapalı | Ses parçalarını da indirin. |
| `--voice` | kapalı | Sesli mesajları da indirin. |
| `--links` | kapalı | Bağlantı önizlemelerini ve URL'leri de kaydedin. |
| `--gifs` | kapalı | GIF animasyonlarını da indirin. |
| `--members` | kapalı | Konuşma katılımcılarının listesini de kaydedin. |
| `--estimate` | kapalı | Yedeğin ne kadar süreceğini gösterin, ardından durun. Hiçbir şey indirilmez. |
| `--count` | kapalı | Kaç mesaj ve dosya olduğunu gösterin, ardından durun. Hiçbir şey indirilmez. |

**Örnekler:**

| Platform | Komut |
|----------|-------|
| **Windows** | `telegram-cli backup -1001234567890 --limit=500` |
| **macOS** | `./telegram-cli backup -1001234567890 --limit=500` |
| **Python** | `python3 telegram-cli.pyz backup -1001234567890 --limit=500` |

**Beklenen sonuç** (yalnızca mesajlar):

```
✓ 500 messages saved to synchromessotron/Telegram_777000/2026/
```

**Beklenen sonuç** (`--media --files` ile):

```
✓ 500 messages saved to synchromessotron/Telegram_777000/2026/
✓ 23 media files downloaded
✓ 7 documents downloaded
```

**Artımlı yedekleme** — yalnızca bir tarihten sonraki mesajlar:

```
telegram-cli backup -1001234567890 --since=2026-03-01
```

**Beklenen sonuç:**

```
✓ 12 messages saved to synchromessotron/Telegram_777000/2026/03/
```

**Zaman aralığı** — iki tarih arasındaki mesajlar (`--since`, `--upto`'dan önce olmalıdır):

```
telegram-cli backup -1001234567890 ^
    --since=2026-01-01T00 ^
    --upto=2026-01-01T10
```

> **Yaygın hata:** `--since` değerinin `--upto`'dan *sonra* bir tarihe ayarlanması 0 mesaj kaydedilmesiyle sonuçlanır; çünkü hiçbir mesaj hem Şubat'tan sonra hem de Ocak'tan önce olamaz. Her zaman `--since` değerinin `--upto`'dan daha eski bir tarih olduğunu kontrol edin.

**Büyük bir yedeklemeden önce süre tahmini:**

```
telegram-cli backup -1001234567890 --limit=5000 --estimate
```

**Beklenen sonuç:**

```
≈ 12 minutes (5000 messages, estimated 2.4 ms per message)
```

Tahmin yaklaşıktır — gerçek süre internet hızınıza ve Telegram sınırlarına bağlıdır. Hiçbir şey indirilmez.

**İndirmeden önce mesaj sayısını görüntüleyin:**

```
telegram-cli backup -1001234567890 --count
```

**Beklenen sonuç:**

```
Messages: 350 total
  photo: 42
  link/webpage: 8
  video: 5
  file/document: 2
```

Bir sorun oluşursa: `ENTITY_NOT_FOUND`, `NETWORK_ERROR`, `PERMISSION_DENIED`, `RATE_LIMITED`. Bkz. [Hata İşleme](#hata-işleme).

---

### send — Mesaj gönderin

```
send <dialog_id> --text=TEXT
```

**Parametreler:**

| Parametre | Açıklama |
|-----------|----------|
| `<dialog_id>` | Konuşma kimliği (zorunlu). |
| `--text` | Gönderilecek metin (zorunlu). |

**Örnekler:**

| Platform | Komut |
|----------|-------|
| **Windows** | `telegram-cli send -1001234567890 --text="Hello from CLI!"` |
| **macOS** | `./telegram-cli send -1001234567890 --text="Hello from CLI!"` |
| **Python** | `python3 telegram-cli.pyz send -1001234567890 --text="Hello from CLI!"` |

**Beklenen sonuç:**

```
✓ Message sent
  ID:    12345
  Date:  2026-03-16 14:30:00
  Text:  Hello from CLI!
```

Bir sorun oluşursa: `ENTITY_NOT_FOUND`, `PERMISSION_DENIED`, `RATE_LIMITED`. Bkz. [Hata İşleme](#hata-işleme).

---

### edit — Bir mesajı düzenleyin

```
edit <dialog_id> <message_id> --text=TEXT
```

**Parametreler:**

| Parametre | Açıklama |
|-----------|----------|
| `<dialog_id>` | Konuşma kimliği (zorunlu). |
| `<message_id>` | Mesaj kimliği (zorunlu). |
| `--text` | Yeni mesaj metni (zorunlu). |

**Örnekler:**

| Platform | Komut |
|----------|-------|
| **Windows** | `telegram-cli edit -1001234567890 42 --text="Corrected text"` |
| **macOS** | `./telegram-cli edit -1001234567890 42 --text="Corrected text"` |
| **Python** | `python3 telegram-cli.pyz edit -1001234567890 42 --text="Corrected text"` |

**Beklenen sonuç:**

```
✓ Message edited
  ID:    42
  Date:  2026-03-16 14:30:00
  Text:  Corrected text
```

Bir sorun oluşursa: `ENTITY_NOT_FOUND`, `NOT_MODIFIED`, `PERMISSION_DENIED`. Bkz. [Hata İşleme](#hata-işleme).

---

### delete — Mesajları silin

```
delete <dialog_id> <message_id> [<message_id> ...]
```

**Parametreler:**

| Parametre | Açıklama |
|-----------|----------|
| `<dialog_id>` | Konuşma kimliği (zorunlu). |
| `<message_id>` | Bir veya daha fazla mesaj kimliği (zorunlu). |

**Örnekler:**

| Platform | Komut |
|----------|-------|
| **Windows** | `telegram-cli delete -1001234567890 42 43 44` |
| **macOS** | `./telegram-cli delete -1001234567890 42 43 44` |
| **Python** | `python3 telegram-cli.pyz delete -1001234567890 42 43 44` |

**Beklenen sonuç:**

```
✓ 3 messages deleted
```

Bir sorun oluşursa: `ENTITY_NOT_FOUND`, `PERMISSION_DENIED`. Bkz. [Hata İşleme](#hata-işleme).

---

### download-media — Fotoğraf, video veya dosya indirin

```
download-media <dialog_id> <message_id> [--outdir=DIR]
```

**Parametreler:**

| Parametre | Varsayılan | Açıklama |
|-----------|------------|----------|
| `<dialog_id>` | — | Konuşma kimliği (zorunlu). |
| `<message_id>` | — | Mesaj kimliği (zorunlu). |
| `--outdir` | `./synchromessotron` | Varsayılan yerine bu klasöre kaydedin. |

Dosya, konuşma klasörünün içindeki uygun alt klasöre kaydedilir (`media/`, `files/`, `music/`, `voice/`, `gifs/`).

**Örnekler:**

| Platform | Komut |
|----------|-------|
| **Windows** | `telegram-cli download-media -1001234567890 42` |
| **macOS** | `./telegram-cli download-media -1001234567890 42` |
| **Python** | `python3 telegram-cli.pyz download-media -1001234567890 42` |

**Beklenen sonuç:**

```
✓ Downloaded: synchromessotron/Telegram_777000/2026/03/media/photo_42.jpg (2.1 MB)
```

Bir sorun oluşursa: `ENTITY_NOT_FOUND`, `NETWORK_ERROR`, `PERMISSION_DENIED`. Bkz. [Hata İşleme](#hata-işleme).

---

### ping — Telegram'ın erişilebilir olup olmadığını kontrol edin

```
ping
```

Parametre yok.

**Örnekler:**

| Platform | Komut |
|----------|-------|
| **Windows** | `telegram-cli ping` |
| **macOS** | `./telegram-cli ping` |
| **Python** | `python3 telegram-cli.pyz ping` |

**Beklenen sonuç:**

```
✓ Telegram is reachable (42.3 ms)
```

Bir sorun oluşursa: `NETWORK_ERROR`. Bkz. [Hata İşleme](#hata-işleme).

---

### whoami — Girişinizi kontrol edin

```
whoami
```

Parametre yok.

**Örnekler:**

| Platform | Komut |
|----------|-------|
| **Windows** | `telegram-cli whoami` |
| **macOS** | `./telegram-cli whoami` |
| **Python** | `python3 telegram-cli.pyz whoami` |

**Beklenen sonuç:**

```
✓ Session valid
  User ID:   123456789
  Name:      Your Name
  Username:  @yourhandle
  Phone:     +1234567890
```

Bir sorun oluşursa: `AUTH_FAILED`, `SESSION_INVALID`. Bkz. [Hata İşleme](#hata-işleme).

---

### help — Yardımı kendi dilinizde görüntüleyin

```
help [LANG] [COMMAND]
```

**Parametreler:**

| Parametre | Varsayılan | Açıklama |
|-----------|------------|----------|
| `LANG` | `en` | Dil kodu. Desteklenenler: `en`, `ru`, `fa`, `tr`, `ar`, `de`. |
| `COMMAND` | — | Belirtilirse yalnızca o komut için yardım gösterilir. |

**Örnekler:**

| Platform | Komut |
|----------|-------|
| **Windows** | `telegram-cli help de backup` |
| **macOS** | `./telegram-cli help de backup` |
| **Python** | `python3 telegram-cli.pyz help de backup` |

**Beklenen sonuç** (genel, İngilizce):

```
telegram-cli — command-line tool for Telegram

Commands:
  init            Set up credentials and session
  whoami          Validate session and show user info
  ping            Check Telegram availability
  get-dialogs     List your dialogs
  backup          Full or incremental message backup
  send            Send a message
  edit            Edit a previously sent message
  delete          Delete own messages
  download-media  Download media from a message
  help            Show this help
  version         Show version information

Run 'telegram-cli help <lang> <command>' for details.
```

---

### version — Sürüm bilgilerini görüntüleyin

```
version
```

Parametre yok.

**Örnekler:**

| Platform | Komut |
|----------|-------|
| **Windows** | `telegram-cli version` |
| **macOS** | `./telegram-cli version` |
| **Python** | `python3 telegram-cli.pyz version` |

**Beklenen sonuç:**

```json
{
  "cli": { "version": "1.0.0", "build": 1, "datetime": "2026-03-17T00:00:00Z" },
  "lib": { "version": "1.2.0", "build": 3, "datetime": "2026-03-18T00:00:00Z" }
}
```

---

## Hata İşleme

Bir sorun oluştuğunda telegram-cli, sorunu ve ne yapmanız gerektiğini açıklayan bir mesaj yazdırır.

Örnek:

```
Error [RATE_LIMITED]: Too many requests — retry after 30s
  retry_after: 30
```

**Her hatanın anlamı ve yapmanız gerekenler:**

| Hata | Ne oldu | Ne yapmalısınız |
|------|---------|-----------------|
| `AUTH_FAILED` | Telegram hesabınız devre dışı bırakılmış veya yasaklanmıştır. | Telegram desteğiyle iletişime geçin. |
| `ENTITY_NOT_FOUND` | Kullandığınız konuşma veya mesaj kimliği mevcut değil. | Doğru kimliği bulmak için `get-dialogs` kullanın. |
| `INTERNAL_ERROR` | telegram-cli içinde beklenmeyen bir hata oluştu. | Sorunu bildirin ve tam hata mesajını ekleyin. |
| `NETWORK_ERROR` | telegram-cli, Telegram'a ulaşamıyor. | İnternet bağlantınızı kontrol edin veya daha sonra tekrar deneyin. |
| `NOT_MODIFIED` | Bir mesajı düzenlemeye çalıştınız, ancak yeni metin eskisiyle aynı. | Farklı bir metin kullanın. |
| `PERMISSION_DENIED` | Bu konuşmayı okuma veya yazma izniniz yok. | O konuşma için erişim haklarınızı kontrol edin. |
| `RATE_LIMITED` | Kısa sürede çok fazla istek gönderdiniz; Telegram beklemenizi istiyor. | Hata mesajında belirtilen saniye kadar bekleyin, ardından tekrar deneyin. |
| `SESSION_INVALID` | Giriş oturumunuzun süresi dolmuş veya iptal edilmiştir. | Yeniden giriş yapmak için tekrar `telegram-cli init` çalıştırın. |

## Çıkış Kodları

telegram-cli tamamlandığında işletim sistemine bir sayı döndürür (betikler için kullanışlıdır):

| Kod | Anlam |
|-----|-------|
| 0 | Her şey çalıştı. |
| 1 | Yanlış bir komut veya parametre kullandınız. |
| 2 | Bir Telegram hatası oluştu (yukarıdaki tabloya bakın). |

---

## Gelişmiş

### `--split_threshold` ile klasör derinliğini kontrol etme

Varsayılan olarak mesajlar yıllık klasörlerde gruplandırılır. Bir yılda çok sayıda mesaj varsa telegram-cli otomatik olarak içinde aylık alt klasörler oluşturur; gerekirse günlük, saatlik ve dakikalık alt klasörler de oluşturabilir.

Daha derin bir bölümlemeyi tetikleyen eşik değeri `--split_threshold` (varsayılan: `100`) ile kontrol edilir. Örneğin `--split_threshold=20` ile bir yedekleme çalıştırırsanız, bir klasör 20'den fazla mesaj içereceği zaman yeni bir alt klasör düzeyi oluşturulur.

```
telegram-cli backup -1001234567890 --split_threshold=20
```

Bu, çok aktif konuşmalar için daha ayrıntılı bir düzenleme istediğinizde kullanışlıdır. Çoğu kullanıcı için varsayılan değer yeterlidir.

Derinlik şu sırayı izler:

```
year/ → month/ → day/ → hour/ → minute/
```

Mesajlar her zaman en derin düzeyde saklanır — iki düzeye bölünmez.

---

## Sorun Giderme

### telegram-cli, Telegram'a ulaşamıyor

`NETWORK_ERROR` görüyorsanız, Telegram bilgisayarınızdan erişilemez durumdadır.

**Şu adımları sırayla deneyin:**

1. İnternet bağlantınızın çalıştığını kontrol edin (tarayıcıda bir web sitesi açın).
2. Birkaç dakika sonra tekrar deneyin — Telegram geçici bir kesinti yaşıyor olabilir.
3. Telegram bölgenizde engelleniyorsa VPN kullanmayı düşünün.
4. Sorunun bağlantıdan mı yoksa oturumunuzdan mı kaynaklandığını doğrulamak için `telegram-cli ping` çalıştırın.

---

### Yazma izni hatası

telegram-cli çıktı klasörüne yazamadığını söylüyorsa, kullanıcı hesabınızın orada dosya oluşturma izni yoktur.

**Çoğu kullanıcı için en kolay çözüm:** telegram-cli'yi ana klasörünüzden veya Masaüstünden çalıştırın ya da ana dizininizdeki bir klasöre işaret etmek için `--outdir` kullanın. Bu konumların her zaman yazma izni vardır.

**Windows — yazma iznini kontrol edin ve verin:**

Hedef klasöre sağ tıklayın → **Özellikler** → **Güvenlik** sekmesi → kullanıcınızın **Yazma** iznine sahip olduğunu kontrol edin. Yoksa **Düzenle**'ye tıklayın, kullanıcınızı seçin ve **Yazma** kutusunu işaretleyin.

İleri düzey kullanıcılar için aynı işlem Komut İstemi'nde de yapılabilir:

```
icacls "C:\path\to\folder"
```

Kullanıcı adınızın yanında `(W)` veya `(F)` olup olmadığını kontrol edin. Yazma izni vermek için:

```
icacls "C:\path\to\folder" /grant %USERNAME%:W
```

**macOS / Linux — yazma iznini kontrol edin ve verin:**

Ana dizininizdeki klasörlerin (Masaüstü, Belgeler, İndirilenler) çoğunun zaten yazma izni vardır. Özel bir yol kullanıyorsanız şununla kontrol edin:

```
ls -ld /path/to/folder
```

İzinlerde `w` yoksa şununla ekleyin:

```
chmod u+w /path/to/folder
```

---

### Giriş kodu gelmiyor

`telegram-cli init` çalıştırdıktan sonra giriş kodu gelmezse:

1. Girdiğiniz telefon numarasının doğru olduğundan ve ülke kodunu içerdiğinden emin olun (örn. `+905551234567`).
2. Telegram uygulamanızı kontrol edin — kod, resmi Telegram hesabından normal bir Telegram mesajı olarak gelir.
3. Bir dakika bekleyin ve `telegram-cli init` komutunu tekrar çalıştırın.

---

### Oturum süresi dolmuş

`SESSION_INVALID` görüyorsanız, girişinizin süresi dolmuş veya iptal edilmiştir (örneğin Telegram ayarlarında tüm aktif oturumları sonlandırdıysanız).

Yeniden giriş yapmak için `telegram-cli init` komutunu çalıştırın.
