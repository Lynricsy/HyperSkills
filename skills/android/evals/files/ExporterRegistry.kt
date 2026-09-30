// app/src/main/java/com/example/ledger/export/ExporterRegistry.kt
package com.example.ledger.export

interface Exporter {
    fun export(entries: List<LedgerEntry>): ByteArray
}

data class LedgerEntry(val id: Long, val amountMinor: Long, val memo: String)

class CsvExporter : Exporter {
    override fun export(entries: List<LedgerEntry>): ByteArray =
        entries.joinToString("\n") { "${it.id},${it.amountMinor},${it.memo}" }.toByteArray()
}

class OfxExporter : Exporter {
    override fun export(entries: List<LedgerEntry>): ByteArray = TODO_OFX_HEADER.toByteArray()

    private companion object {
        const val TODO_OFX_HEADER = "OFXHEADER:100"
    }
}

object ExporterRegistry {
    // Remote config delivers e.g. "com.example.ledger.export.CsvExporter".
    fun create(className: String): Exporter =
        Class.forName(className).getDeclaredConstructor().newInstance() as Exporter
}
