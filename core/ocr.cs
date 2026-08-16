using System;
using System.IO;
using System.Threading.Tasks;
using Windows.Media.Ocr;
using Windows.Graphics.Imaging;
using Windows.Storage;

class Program {
    static async Task MainAsync(string path) {
        StorageFile file = await StorageFile.GetFileFromPathAsync(path);
        using (var stream = await file.OpenAsync(FileAccessMode.Read)) {
            BitmapDecoder decoder = await BitmapDecoder.CreateAsync(stream);
            SoftwareBitmap bitmap = await decoder.GetSoftwareBitmapAsync();

            OcrEngine engine = null;
            if (OcrEngine.AvailableRecognizerLanguages.Count > 0) {
                engine = OcrEngine.TryCreateFromLanguage(OcrEngine.AvailableRecognizerLanguages[0]);
            }
            if (engine == null) return;

            OcrResult result = await engine.RecognizeAsync(bitmap);
            Console.OutputEncoding = System.Text.Encoding.UTF8;
            Console.WriteLine(result.Text);
        }
    }

    static void Main(string[] args) {
        if (args.Length == 0) return;
        try {
            MainAsync(args[0]).GetAwaiter().GetResult();
        } catch (Exception ex) {
            Console.Error.WriteLine(ex.Message);
        }
    }
}
