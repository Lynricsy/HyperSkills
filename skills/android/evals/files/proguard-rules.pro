# app/proguard-rules.pro
# Exporters are looked up by class name from remote config (see ExporterRegistry.kt).
-keep class com.example.ledger.export.CsvExporter
-keep class com.example.ledger.export.OfxExporter
