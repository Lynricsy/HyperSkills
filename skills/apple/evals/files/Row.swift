import SwiftUI

struct Item {
    var id = UUID()
    var title: String
    var subtitle: String
}

@Observable
final class LibraryModel {
    var items: [Item] = []
    var filterText = ""

    func refresh() {
        items = items.sorted { $0.title < $1.title }
    }
}

struct Row: View {
    @State var item: Item
    var isHighlighted: Bool

    var body: some View {
        HStack {
            Text(item.title)
                .foregroundColor(isHighlighted ? .red : .primary)
            Spacer()
            Button(action: { item.title = item.title.uppercased() }) {
                Image(systemName: "textformat")
            }
        }
        .padding()
        .animation(.default)
    }
}

struct LibraryView: View {
    @State var model = LibraryModel()

    var body: some View {
        NavigationStack {
            VStack {
                header
                List {
                    ForEach(model.items.indices, id: \.self) { index in
                        Row(item: model.items[index], isHighlighted: index == 0)
                    }
                }
                footer
            }
            .navigationTitle("Library")
        }
    }

    private var header: some View {
        TextField("Filter", text: Binding(
            get: { model.filterText },
            set: { model.filterText = $0; model.refresh() }
        ))
        .padding(.horizontal)
    }

    private var footer: some View {
        HStack {
            Text("\(model.items.count) items")
            Spacer()
            Text(model.items.first?.title ?? "")
        }
        .padding(.horizontal)
    }
}
