fn get_element(arr: &[i32], index: usize) -> Option<i32> {
    arr.get(index).copied()
}

fn main() {
    let numbers = [1, 2, 3, 4, 5];
    match get_element(&numbers, 10) {
        Some(element) => println!("Element: {}", element),
        None => println!("Error: Index out of bounds"),
    }
}