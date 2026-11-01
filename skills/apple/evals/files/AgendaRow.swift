import SwiftUI

struct AgendaItem: Identifiable, Decodable {
    let id: UUID
    let title: String
    let due: String // ISO 8601 from the server, e.g. "2026-11-03T09:00:00Z"
}

struct AgendaRow: View {
    let item: AgendaItem

    var body: some View {
        HStack {
            Text(item.title)
                .foregroundColor(.primary)
            Spacer()
            Text(dueText)
                .foregroundColor(.secondary)
        }
        .padding(8)
        .background(Color.yellow.opacity(0.2))
        .cornerRadius(8)
    }

    private var dueText: String {
        let date = Date(item.due, strategy: .iso8601)
        return date.formatted(date: .abbreviated, time: .omitted)
    }
}

struct AgendaRow_Previews: PreviewProvider {
    static var previews: some View {
        AgendaRow(item: AgendaItem(id: UUID(), title: "Dentist", due: "2026-11-03T09:00:00Z"))
    }
}
