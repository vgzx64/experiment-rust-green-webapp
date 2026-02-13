// Fixed: Safe version with bounds checking
fn get_element(arr: &[i32], index: usize) -> Option<i32> {
    arr.get(index).copied()
}

fn main() {
    let numbers = [1, 2, 3, 4, 5];
    match get_element(&numbers, 10) {
        Some(value) => println!("Element: {}", value),
        None => println!("Index out of bounds!"),
    }
}
