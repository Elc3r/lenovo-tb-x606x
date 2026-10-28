// SPDX-License-Identifier: Apache-2.0
#include <fstream>
#include <iostream>
#include <iterator>
#include <property_info_serializer/property_info_serializer.h>
#include <property_info_parser/property_info_parser.h>
using namespace android::properties;
int main(int argc, char** argv) {
  std::vector<PropertyInfoEntry> entries;
  for (int i = 1; i < argc; ++i) {
    std::ifstream f(argv[i]); if (!f) return 2;
    std::string text((std::istreambuf_iterator<char>(f)), {});
    std::vector<std::string> errors;
    ParsePropertyInfoFile(text, false, &entries, &errors);
    if (!errors.empty()) return 3;
  }
  std::string data, error;
  if (!BuildTrie(entries, "u:object_r:default_prop:s0", "string", &data, &error)) return 4;
  auto* area = reinterpret_cast<const PropertyInfoArea*>(data.data());
  std::string name;
  while (std::getline(std::cin, name)) {
    const char *context = nullptr, *type = nullptr;
    area->GetPropertyInfo(name.c_str(), &context, &type);
    std::cout << name << '\t' << (context ? context : "") << '\t' << (type ? type : "") << '\n';
  }
}
